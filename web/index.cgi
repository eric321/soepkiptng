#!/usr/bin/perl

############################################################################
# soepkiptng (c) copyright 2000 Eric Lammerts <eric@lammerts.org>.
# $Id$

############################################################################
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.

############################################################################
# CONFIG

BEGIN {
	$configfile = "/etc/soepkiptng.conf";
	my $f;

	local *F;
	open F, $configfile or die "$configfile: $!\n";
	while(<F>) {
		/^#/ and next;
		s/\s+$//;
		/./ or next;
		if(/^(\w+)\s*=\s*(.*?)\s*$/) {
			$f = $1;
			${$f} = $2;
		} elsif(/^\s+(.*?)\s*$/) {
			# continuation line
			${$f} .= "\n$1";
		} else {
			die "$configfile line $.: invalid format\n";
		}
	}
	close F;

	require "$progdir/soepkiptng.lib";
}


############################################################################
# SUBROUTINES

sub encode($) {
	my ($a) = @_;

	$a =~ s|([^-./\w])|sprintf "%%%02x", ord($1)|ge;
#	$a =~ s| |+|g;
	$a;
}

sub decode($) {
	my ($a) = @_;

	$a =~ s|\+| |g;
	$a =~ s|%([0-9a-f][0-9a-f])|chr(hex($1))|ge;
	$a;
}

sub can_delete($) {
	my ($file) = @_;

	my $dir = $file;
	$dir =~ s|[^/]*$||;
	return 1 if -w $dir;
	return 1 if -k $dir && -w $file;
}

sub print_frame() {
	print <<EOF;
<html>
<head>
<title>$title</title>
</head>
<frameset rows="$frameheights" frameborder=yes>
 <frame name=tframe src="$self?cmd=playlist" marginheight="$marginheight">
 <frame name=bframe src="$self?cmd=empty" marginheight="$marginheight">
</frameset>
<body $body>
</body>
</html>
EOF
}

sub print_az_table($$) {
	my ($dbh, $session) = @_;
	my ($playlistopts, $editlistopts);

	my $sth = $dbh->prepare("SELECT id,name FROM list ORDER BY name");
	$sth->execute;
	while($_ = $sth->fetchrow_hashref) {
		$playlistopts .= sprintf("   <option value=%d%s>%s\n", $_->{id},
			$_->{id} == $$session{'playlist'}? " selected":"", $_->{name});
		$editlistopts .= sprintf("   <option value=%d%s>%s\n", $_->{id},
			$_->{id} == $$session{'editlist'}? " selected":"", $_->{name});
	}


	print <<EOF;
<table cellpadding=0 cellspacing=0><tr><td id=az nowrap>
<a id=a href="$self?cmd=playlist">Refresh</a>&nbsp;&nbsp;
EOF
	$_ = encode("^[^a-zA-Z]");
	print qq|<a id=a href="$self?cmd=$artistlistcmd&artist=$_" target=bframe>0-9</a>&nbsp;|;
	foreach('A'..'Z') {
		my $e = encode("^$_");
		print qq|<a id=a href="$self?cmd=$artistlistcmd&artist=$e" target=bframe>$_</a>&nbsp;|;
	}
	print <<EOF;
</td>
<td id=az nowrap>Artist:</td>
<td id=az nowrap>
 <form id=search action="$self" method=get target=bframe>
  <input type=hidden name=cmd value=$artistlistcmd>
  <input type=hidden name=cap value="Artist search: %s">
   <input type=text size=5 name=artist style="$searchformstyle">
 </form>
</td>
<td id=az nowrap>Album:</td>
<td id=az>
 <form id=search action="$self" method=get target=bframe>
  <input type=hidden name=cap value="Album search: %s">
  <input type=hidden name=cmd value=artistlist>
   <input type=text size=5 name=album style="$searchformstyle">
 </form>
</td>
<td id=az nowrap>Title:</td>
<td id=az>
 <form id=search action="$self" method=get target=bframe>
  <input type=hidden name=cap value="Song search: %s">
 <input type=hidden name=cmd value=alllist>
   <input type=text size=5 name=title style="$searchformstyle">
 </form>
</td>

<!--
<td id=az>Play:</td>
<td id=az>
  <form id=search action="$self" method=get target=tframe>
  <select name=list onChange="">
   <option value="">All
$playlistopts
  </select>
  <input type=hidden name=cmd value=setplaylist>
  <input type=submit value="Ok">
  </form>
</td>

<td id=az>Edit:</td>
<td id=az>
  <form id=search action="$self" method=get target=tframe>
  <select name=list onChange="">
   <option value="">
$editlistopts
  </select>
  <input type=hidden name=cmd value=seteditlist>
  <input type=submit value="Ok">
  </form>
</td>

<td id=az>&nbsp;&nbsp;
<a id=a target=bframe href="$self?cmd=lists">Playlists</a>
</td>
-->

<td id=az>&nbsp;&nbsp;
<a id=a target=_blank href="$self?cmd=maint">Maintenance</a>
</td>
<td id=az>&nbsp;&nbsp;
<a id=a href="$self?cmd=shuffle">Shuffle</a>
</td>
<td id=az>&nbsp;&nbsp;
<a id=a href="$self?cmd=recent&days=7" target=bframe>Recent</a>
</td>
</tr></table>
EOF
}


sub get_playlist_table_entry($$$$$) {
	my $l = sprintf "%d:%02d", $_[4]->{length} / 60, $_[4]->{length} % 60;
	my $e = $_[4]->{encoding};
	$e =~ s/ /&nbsp;/g;
	my $tr = $_[4]->{track} || "";
	$tr .= "." if $tr;
	my $fmt = <<EOF;
 <tr>
  <td $td_left>&nbsp;<a id=a href="%s">%s</a> <a id=a href="%s">%s</a>&nbsp;</td>
  <td $td_artist>&nbsp;<a href="$self?cmd=alllist&artist_id=$_[4]->{arid}&cap=%s" target=bframe>%s</a>&nbsp;</td>
  <td $td_album>&nbsp;<a href="$self?cmd=alllist&album_id=$_[4]->{alid}&cap=%s" target=bframe>%s</a>&nbsp;</td>
  <td $td_track>&nbsp;%s&nbsp;</td>
  <td $td_song>&nbsp;%s&nbsp;</td>
  <td $td_time>&nbsp;%s&nbsp;</td>
  <td $td_enc>&nbsp;%s&nbsp;</td>
  <td $td_edit>&nbsp;<a id=a href="$self?cmd=edit&id=%d" target=bframe>*</a></td>
 </tr>
EOF
	return sprintf $fmt, $_[0], $_[1], $_[2], $_[3],
		encode("Artist: $_[4]->{artist}"), $_[4]->{artist},
		encode("Album: $_[4]->{album}"), $_[4]->{album},
		$tr, $_[4]->{title}, $l, $e, $_[4]->{id};
}

sub print_playlist_table($$) {
	my ($dbh, $nowplaying) = @_;
	my $nowfile;
	my $output;
	my $delall;

	if(!$nowplaying) {
		local *F;
		if(open F, $statusfile) {
			$nowplaying = <F>;
			$nowfile = <F>;
			close F;
		}
	}
	if($nowplaying) {
		my $query =  "SELECT title,artist.name as artist,album.name as album," .
			"song.id as id,track,length,encoding," .
			"song.artist_id as arid,song.album_id as alid" .
			" FROM song,artist,album" .
			" WHERE song.artist_id=artist.id AND song.album_id=album.id" .
			" AND song.id = $nowplaying";
		my $sth = $dbh->prepare($query);
		my $rv = $sth->execute;
		$_ = $sth->fetchrow_hashref or do {
			$nowfile =~ m|(.*/)?(.*)|;
			$_->{artist} = 'ERROR: Not in database';
			$_->{album} = $1;
			$_->{title} = $2;
			$_->{id} = $nowplaying;
			$_->{track} = '';
			$_->{length} = 0;
			$_->{encoding} = '?';
		};
		$output .= get_playlist_table_entry
			"$self?cmd=kill", $killtext, "", "", $_;
	}

	$query =  "SELECT title,artist.name as artist,album.name as album,song.id as id,track,length,encoding," .
		"song.artist_id as arid,song.album_id as alid" .
		" FROM song,queue,artist,album" .
		" WHERE song.artist_id=artist.id AND song.album_id=album.id" .
		" AND song.id = queue.song_id ORDER BY queue.song_order";
	$sth = $dbh->prepare($query);
	$rv = $sth->execute;
	my @ids;
	while($_ = $sth->fetchrow_hashref) {
#		next if $_->{id} == $nowplaying;
		push @ids, $_->{id};
		$output .= get_playlist_table_entry
			"$self?cmd=del&id=$_->{id}", $deltext,
			"$self?cmd=up&id=$_->{id}", $uptext,
			$_;
	}
	if(@ids) {
		$delall = sprintf <<EOF, join(",", @ids);
<a id=a href="$self?cmd=del&id=%s">$delalltext</a>
EOF
	}
	print <<EOF;
<table border=0 cellspacing=0>
 <tr>
  <th $th_left>&nbsp;$delall&nbsp;</th>
  <th $th_artist>&nbsp;Artist&nbsp;</th>
  <th $th_album>&nbsp;Album&nbsp;</th>
  <th $th_track>&nbsp;#&nbsp;</th>
  <th $th_song>&nbsp;Song&nbsp;</th>
  <th $th_time>&nbsp;Time&nbsp;&nbsp;</th>
  <th $th_enc>&nbsp;Encoding&nbsp;</th>
  <th $th_edit>&nbsp;&nbsp;</th>
 </tr>
 <tr><td colspan=7></td></tr>
$output
</table>
EOF
}

sub print_artistlist_table($$$$) {
	my ($dbh, $session, $field, $val) = @_;

	printf <<EOF, ucfirst($field) . ": $val";
<center id=hdr>%s</center>
<table border=0 cellspacing=0>
 <tr>
  <th>&nbsp;Artist&nbsp;</th>
  <th>&nbsp;Albums&nbsp;</th>
 </tr>
EOF

	my $query = "SELECT DISTINCT artist.name as artist, album.name as album," .
			" count(*), song.artist_id, song.album_id," .
			" UCASE(album.name) as sort" .
			" FROM song,artist,album WHERE present AND $field.name REGEXP ?".
			" AND song.artist_id=artist.id AND song.album_id=album.id".
			" GROUP BY binary artist.name, binary album.name ORDER BY sort";
	my $sth = $dbh->prepare($query);
	my $rv = $sth->execute($val)
		or die "can't do sql command: " . $dbh->errstr . "\n";
	my ($ar, $al, $c, $arid, $alid);
	my %artistname;
	my %al;
	while(($ar, $al, $c, $arid, $alid) = $sth->fetchrow_array) {
		$artistname{$arid} = $ar;
		if($al) {
			$al =~ /(.?)(.*)/;
			$al{$arid} .= sprintf(<<EOF, encode("Album: $al"), $1, $2, $c);
<a id=a href="$self?cmd=alllist&album_id=$alid&cap=%s"><b>%s</b>%s</a> (%d)&nbsp;&nbsp;
EOF
		} else {
			$al{$arid} .= sprintf(<<EOF, encode("Artist: $a; Album: ?"), $c);
<a id=a href="$self?cmd=alllist&artist_id=$arid&album_id=$alid&cap=%s"><b>?</b></a> (%d)&nbsp;&nbsp;
EOF
		}
	}
	foreach(sort {lc($artistname{$a}) cmp lc($artistname{$b})} keys %artistname) {
		$al{$_} =~ s/, $//;
		printf <<EOF, encode("Artist: $artistname{$_}"), $artistname{$_}, $al{$_};
<tr>
 <td>&nbsp;<a id=a href="$self?cmd=alllist&artist_id=$_&cap=%s">%s</a>&nbsp;</td>
 <td>&nbsp;%s&nbsp;</td>
</tr>
EOF
	}
	print <<EOF;
</table>
EOF
}

sub print_alllist_table($$$@) {
	my ($dbh, $argsref, $session, $caption, $query, @val) = @_;
	my ($output, $addall);

	my $sth = $dbh->prepare($query);
	my $rv = $sth->execute(@val);
	my @ids;
	my %artistids;
	while($_ = $sth->fetchrow_hashref) {
		push @ids, $_->{id};
		$artistids{$_->{arid}}++;
		my $l = sprintf "%d:%02d", $_->{length} / 60, $_->{length} % 60;
		my $e = $_->{encoding};
		$e =~ s/ /&nbsp;/g;
		my $tr = $_->{track} || "";
		$tr .= "." if $tr;
		my $fmt = <<EOF;
 <tr>
  <td $td_left>&nbsp;<a id=a href="$self?cmd=add&id=%d" target=tframe>$addtext</a>&nbsp;</td>
  <td $td_artist>&nbsp;<a id=a href="$self?cmd=alllist&artist_id=$_->{arid}&cap=%s">%s</a>&nbsp;</td>
  <td $td_album>&nbsp;<a id=a href="$self?cmd=alllist&album_id=$_->{alid}&cap=%s">%s</a>&nbsp;</td>
  <td $td_track>&nbsp;%s&nbsp;</td>
  <td $td_song>&nbsp;<a id=a href="$self?cmd=add&id=%d" target=tframe>%s</a>&nbsp;</td>
  <td $td_time>&nbsp;%s&nbsp;</td>
  <td $td_enc>&nbsp;%s&nbsp;</td>
  <td $td_edit> <a id=a href="$self?cmd=edit&id=%d" title="Edit">*</a>%s</td>
 </tr>
EOF
		my $el = $$session{'editlist'};
		my $listch;
		if($el) {
			if($dbh->do("SELECT entity_id FROM list_contents" .
				" WHERE list_id=? AND (" .
				"  (type=? AND entity_id=?) OR" .
				"  (type=? AND entity_id=?) OR" .
				"  (type=? AND entity_id=?))", undef,
				$el,
				"Song", $_->{id},
				"Artist", $_->{arid},
				"Album", $_->{alid}) < 1) {
				my $baseurl = "$self?";
				foreach(keys %$argsref) {
					next if $_ eq "cmd";
					next if /^add_/;
					$baseurl .= "$_=" . encode($$argsref{$_}) . "&";
				}
				$listch = <<EOF;
&nbsp;<a href="${baseurl}cmd=addtolist&add_list=$el&add_type=song&add_id=$_->{id}" target=bframe>+</a>
EOF
			}
		}
		$output .= sprintf $fmt, $_->{id},
			encode("Artist: $_->{artist}"), $_->{artist},
			encode("Album: $_->{album}"), $_->{album},
			$tr, $_->{id}, $_->{title}, $l, $e, $_->{id}, $listch;
	}
	print <<EOF;
<center id=hdr>$caption</center>
EOF
	if(scalar keys %artistids == 1) {
		my $query = "SELECT DISTINCT album.name as album, artist.name as artist, count(*)," .
				"song.artist_id, song.album_id" .
				" FROM song,artist,album WHERE present AND song.artist_id = ?".
				" AND song.artist_id=artist.id AND song.album_id=album.id".
				" GROUP BY binary album.name ORDER BY album.name";
		my $sth = $dbh->prepare($query);
		my $rv = $sth->execute(keys %artistids);
		my ($al, $a, $c, $arid, $alid, @al);
		while(($al, $a, $c, $arid, $alid) = $sth->fetchrow_array) {
			if($al) {
				$al =~ /(.?)(.*)/;
				push @al, sprintf(<<EOF, encode("Album: $al"), $1, $2, $c);
<a id=a href="$self?cmd=alllist&album_id=$alid&cap=%s"><b>%s</b>%s</a> (%d)
EOF
			} else {
				push @al, sprintf(<<EOF, encode("Artist: $a; Album: ?"), $c);
<a id=a href="$self?cmd=alllist&artist_id=$arid&album_id=$alid&cap=%s"><b>?</b></a> (%d)
EOF
			}
		}
		printf "Albums: %s.\n", join(",&nbsp; ", @al);
	}

	print "<table border=0 cellspacing=0>\n";

	if(@ids) {
	$addall = sprintf <<EOF, join(",", @ids);
   <a id=a href="$self?cmd=add&id=%s" target=tframe>$addalltext</a>
EOF
	}

	my %revsort;
	$revsort{$$argsref{'sort'}} = "r_";

	delete $$argsref{'sort'};
	my $baseurl = "$self?";
	foreach(keys %$argsref) {
		$baseurl .= "$_=" . encode($$argsref{$_}) . "&";
	}

	print <<EOF;
 <tr>
  <th $th_left>&nbsp;$addall&nbsp;</th>
  <th $th_artist>&nbsp;<a href="${baseurl}sort=$revsort{'artist'}artist">Artist</a>&nbsp;</th>
  <th $th_album>&nbsp;<a href="${baseurl}sort=$revsort{'album'}album">Album</a>&nbsp;</th>
  <th $th_track>&nbsp;<a href="${baseurl}sort=$revsort{'track'}track">#</a>&nbsp;</th>
  <th $th_song>&nbsp;<a href="${baseurl}sort=$revsort{'title'}title">Song</a>&nbsp;</th>
  <th $th_time>&nbsp;<a href="${baseurl}sort=$revsort{'length'}length">Time</a>&nbsp;</th>
  <th $th_enc>&nbsp;<a href="${baseurl}sort=$revsort{'encoding'}encoding">Encoding</a>&nbsp;</th>
  <th $th_edit>&nbsp;&nbsp;</th>
 </tr>
 <tr><td colspan=7></td></tr>
$output
</table>
EOF
}

sub print_edit_page($$) {
	my ($dbh, $id) = @_;

	my $sth = $dbh->prepare("SELECT artist.name as artist,album.name as album,song.*," .
		" unix_timestamp(last_played) as lp FROM song,artist,album WHERE song.id=$id" .
		" AND song.artist_id=artist.id AND song.album_id=album.id");
	$sth->execute();
	$_ = $sth->fetchrow_hashref() or die "id $id not found.\n";

	my $l = sprintf "%d:%02d", $_->{length} / 60, $_->{length} % 60;
	my $t = $_->{track} || "";
	my $size = sprintf("%dk", ((-s $_->{filename}) + 512) / 1024);
	my $lp = $_->{lp}? localtime($_->{lp}) : "-";
	my $pr = $_->{present}? "Yes" : "No";
	(my $dir = $_->{filename}) =~ s|/*[^/]+$||;
	(my $file = $_->{filename}) =~ s|.*/||;

	print <<EOF;
<script language="Javascript">
<!--
function verifydelete() {
   return confirm("Are you sure you want to delete this file?");
}
// -->
</script>

<table>
<caption>Edit Song</caption>
<tr>
 <td>
  <form action="$self" method=get>
  <input type=hidden name=id value="$id">
    <input type=hidden name=cmd value=changefile>
  <tr><td>Present:</td><td>$pr</td></tr>
  <tr><td>Artist:</td><td><input type=text size=60 name=artist value="$_->{artist}"></td></tr>
  <tr><td>Title:</td> <td><input type=text size=60 name=title  value="$_->{title}"></td></tr>
  <tr><td>Album:</td> <td><input type=text size=60 name=album  value="$_->{album}"></td></tr>
  <tr><td>Track:</td> <td><input type=text size=3 name=track  value="$t" maxlength=2></td></tr>
  <tr><td>Time:</td>  <td>$l</td></tr>
  <tr><td>Encoding:</td>        <td>$_->{encoding}</td></tr>
  <tr><td>Last played time:</td><td>$lp</td></tr>
  <tr><td>Directory:</td>       <td>$dir</td></tr>
  <tr><td>Filename:</td>        <td>$file</td></tr>
  <tr><td>Size:</td>            <td>$size</td></tr>
  <tr><td colspan=2><input type=submit value="Change"></td></tr>
  </form>
EOF
#<input type=text size=60 name=file value="$file">

	if(can_delete($_->{filename})) {
		print <<EOF;
  <tr><td>
   <form action="$self" method=get onSubmit="return verifydelete();">
    <input type=hidden name=cmd value=delfile>
    <input type=hidden name=id value="$id">
    <input type=submit value="Delete Song">
   </form>
  </td></tr>
EOF
	}
	my $f = $_->{'filename'};
	$f =~ s|.*/||;
	print <<EOF;
  <tr><td>
   <form action="$self/$f" method=post>
    <input type=hidden name=cmd value=download>
    <input type=hidden name=id value="$id">
    <input type=submit value="Download">
   </form>
  </td></tr>
</table>
EOF
}

sub print_lists($) {
	my ($dbh) = @_;

	print <<EOF;
<center id=hdr>Playlists</center>
<table border=0 cellspacing=0>
 <tr>
  <th $th_left>&nbsp</th>
  <th $th_left>&nbsp;Name&nbsp;</th>
  <th $th_left>&nbsp;# Songs&nbsp;</th>
 </tr>
 <tr><td colspan=3></td></tr>

EOF
	my $sth = $dbh->prepare("SELECT id,name FROM list ORDER BY name");
	$sth->execute;
	my $d;
	while($d = $sth->fetchrow_hashref) {
		print <<EOF;
 <tr>
  <td $th_left>&nbsp;<a href="$self?cmd=dellist&id=$d->{id}">del</a>&nbsp;</td>
  <td>&nbsp;<a href="$self?cmd=showlist&id=$d->{id}">$d->{name}</a>&nbsp;</td>
  <td $th_left>&nbsp;88&nbsp;</td>
 </tr>
EOF
	}
	print <<EOF;
</table>
<p>
<form id=search action="$self" method=get target=bframe>
<input type=text size=20 name=listname>
<input type=hidden name=cmd value=addlist>
<input type=submit value="Add Playlist">
</form>
EOF
}

sub printhtmlhdr() {
	my $r = Apache->request;
	$r->content_type("text/html");
	$r->send_http_header;
	print <<EOF;
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">
EOF
}

sub printhdr($) {
	print <<EOF;
<html>
<head>
<style type="text/css">
<!--
$_[0]
-->
</style>
</head>
<body $body>
EOF
}

sub printftr() {
	print <<EOF;
</body>
</html>
EOF
}

sub printredirexit($$$) {
	my ($q, $cmd, $argsref) = @_;
	$$argsref{'cmd'} = $cmd;
 	print $q->redirect(construct_url($q->url(-full=>1), $argsref));
	exit;
}

############################################################################
# MAIN

my $q = new CGI;
$self = $q->url(-absolute=>1);
my %args;
foreach($q->param) { $args{$_} = $q->param($_); }

$SIG{__DIE__} = sub {
	printhtmlhdr;
	print "<p><p>$_[0]\n";
	printhtmlftr;
	exit 0;
};

my $dbh = DBI->connect("DBI:mysql:$db_name:$db_host",$db_user,$db_pass, {mysql_client_found_rows =>1 })
	or die "can't connect to database...$!\n";

# cookies/sessions
my $r = Apache->request;
my $cookie;
if($r->header_in('Cookie') =~ /SESSION_ID=(\w*)/) {
	$cookie = $1;
}
my %session;
tie %session, 'Apache::Session::MySQL', $cookie, {
	Handle     => $dbh,
	LockHandle => $dbh
};
$r->header_out("Set-Cookie" => "SESSION_ID=$session{_session_id};");


my $cmd = $args{'cmd'};

my $r = $refreshtime;
my $nowplaying;

if($cmd eq 'empty') {
	printhtmlhdr;
	print "$bframe_start\n";
	exit;
}

if($cmd eq 'add') {
	add_song($dbh, split(/,/, $args{'id'}));
 	printredirexit($q, 'playlist', undef);
}
elsif($cmd eq 'del') {
	del_song($dbh, split(/,/, $args{'id'}));
 	printredirexit($q, 'playlist', undef);
}
elsif($cmd eq 'up') {
	foreach(reverse split /,/, $args{'id'}) { move_song_to_top($dbh, $_); }
 	printredirexit($q, 'playlist', undef);
}
elsif($cmd eq 'kill') {
	($nowplaying) = kill_song();
 	printredirexit($q, 'playlist', undef);
}
elsif($cmd eq 'setplaylist') {
	$session{'playlist'} = $args{'list'};
 	printredirexit($q, 'playlist', undef);
}
elsif($cmd eq 'seteditlist') {
	$session{'editlist'} = $args{'list'};
 	printredirexit($q, 'playlist', undef);
}
elsif($cmd eq 'addlist') {
	$dbh->do("REPLACE INTO list SET name=?", undef, $args{'listname'})
		or die;
 	printredirexit($q, 'lists', \%args);
}
elsif($cmd eq 'addtolist') {
	$dbh->do("REPLACE INTO list_contents SET type=?, list_id=?, entity_id=?", undef,
		$args{'add_type'}, $args{'add_list'}, $args{'add_id'})
		or die;
	delete $args{'add_type'};
	delete $args{'add_list'};
	delete $args{'add_id'};
 	printredirexit($q, 'alllist', \%args);
}
elsif($cmd eq 'dellist') {
	$dbh->do("DELETE FROM list WHERE id=?", undef, $args{'id'})
		or die;
	$dbh->do("DELETE FROM list_contents WHERE list_id=?", undef, $args{'id'})
		or die;
 	printredirexit($q, 'lists', \%args);
}
elsif($cmd eq 'shuffle') {
	shuffle_queue($dbh);
 	printredirexit($q, 'playlist', \%args);
}
elsif($cmd eq 'changefile') {
	my $arid = get_id($dbh, "artist", $args{'artist'}) or die;
	my $alid = get_id($dbh, "album", $args{'album'}) or die;

	$dbh->do("UPDATE song SET artist_id=?, title=?, album_id=?, track=? WHERE id=?",
		undef, $arid, $args{'title'}, $alid, $args{'track'}, $args{'id'})
		or die "can't do sql command: " . $dbh->errstr . "\n";
 	printredirexit($q, 'edit', \%args);
}



if($cmd eq '') {
	printhtmlhdr;
	print_frame;
}
elsif($cmd eq 'playlist') {
	printhtmlhdr;
	print <<EOF;
<META HTTP-EQUIV="Refresh" CONTENT="$r;URL=$self?cmd=playlist&s=$args{'s'}">
EOF
	printhdr($plstyle);
	print $topwindow_title;
	print_az_table($dbh, \%session);
	print_playlist_table($dbh, $nowplaying);
	printftr;
}
elsif($cmd eq 'artistlist') {
	printhtmlhdr;
	printhdr($artiststyle);
	my $field = $args{'artist'}? 'artist':'album';
	print_artistlist_table($dbh, \%session, $field, $args{$field});
	printftr;
}
elsif($cmd eq 'alllist') {
	printhtmlhdr;
	printhdr($allstyle);
	$args{'f'} =~ /^\w*$/ or die;
	my $q = "SELECT artist.name as artist,album.name as album,song.*," .
		"song.artist_id as arid, song.album_id as alid" .
		" FROM song,artist,album" .
		" WHERE present";
	my @qa;
	my $cap;
	my $s = $args{'sort'};
	$s =~ s/\W//g;
	if($args{'artist'}) {
		$q .= " AND artist.name REGEXP ?";
		push @qa, $args{'artist'};
		$qa[$#qa] =~ s/[^-^\$_0-9a-z]+/.*/ig;
		$s = "artist.name" unless $s;
		$cap = sprintf($args{'cap'}, $args{'artist'});
	}
	if($args{'album'}) {
		$q .= " AND album.name REGEXP ?";
		push @qa, $args{'album'};
		$qa[$#qa] =~ s/[^-^\$_0-9a-z]+/.*/ig;
		$s = "album.name" unless $s;
		$cap = sprintf($args{'cap'}, $args{'album'});
	}
	if($args{'title'}) {
		$q .= " AND title REGEXP ?";
		push @qa, $args{'title'};
		$qa[$#qa] =~ s/[^-^\$_0-9a-z]+/.*/ig;
		$s = "title" unless $s;
		$cap = sprintf($args{'cap'}, $args{'title'});
	}
	if($args{'filename'}) {
		$q .= " AND filename REGEXP ?";
		push @qa, $args{'filename'};
		$qa[$#qa] =~ s/[^-^\$_0-9a-z]+/.*/ig;
		$s = "filename" unless $s;
		$cap = sprintf($args{'cap'}, $args{'filename'});
	}

	if($args{'artist_id'}) {
		$q .= " AND song.artist_id=?";
		push @qa, $args{'artist_id'};
		$s = "artist.name" unless $s;
		$cap = sprintf($args{'cap'}, $args{'artist_id'});
	}
	if($args{'album_id'}) {
		$q .= " AND song.album_id=?";
		push @qa, $args{'album_id'};
		$s = "album.name" unless $s;
		$cap = sprintf($args{'cap'}, $args{'album_id'});
	}

	$s =~ s/^r_(.*)/\1 DESC/;
	$q .= " AND song.artist_id=artist.id AND song.album_id=album.id ".
	      " ORDER BY $s,album.name,track,artist.name,title";
	print_alllist_table($dbh, \%args, \%session, $cap, $q, @qa);
	printftr;
}
elsif($cmd eq 'recent') {
	printhtmlhdr;
	printhdr($allstyle);
	my $maxage = $args{'days'} * 86400;
	my $s = $args{'sort'} || "r_time_added";
	$s =~ s/\W//g;
	$s =~ s/^r_(.*)/\1 DESC/;
	print_alllist_table($dbh, \%args, \%session, "Most recent $n songs",
		"SELECT artist.name as artist,album.name as album,song.*," .
		"song.artist_id as arid, song.album_id as alid" .
		" FROM song,artist,album WHERE present " .
		" AND song.artist_id=artist.id AND song.album_id=album.id" .
		" AND unix_timestamp(now()) - unix_timestamp(time_added) < $maxage" .
		" ORDER BY $s LIMIT 500");
	printftr;
}
elsif($cmd eq 'maint') {
	printhtmlhdr;
	printhdr($allstyle);
	print <<EOF;
<a href="$self?cmd=update">Quick update</a> (leave existing files alone).<br>
<a href="$self?cmd=update&args=-f">Full update</a> (re-enter info for existing files).<br>
EOF
	printftr;
}
elsif($cmd eq 'update') {
	printhtmlhdr;
	printhdr($allstyle);
	print "<pre>\n";
	print `$progdir/soepkiptng_update $args{'args'} 2>/dev/null`;
	print "</pre>\n";
	printftr;
}
elsif($cmd eq 'edit') {
	printhtmlhdr;
	printhdr($editstyle);
	print_edit_page($dbh, $args{'id'});
	printftr;
}
elsif($cmd eq 'delfile') {
	printhtmlhdr;
	printhdr($allstyle);
	$args{'id'} =~ /(\d+)/;
	my $id = $1;
	my ($file) = $dbh->selectrow_array("SELECT filename FROM song WHERE id=$id")
		or die "id $id not found in database\n";
	if(unlink $file) {
		print "$file deleted from disk.\n";
		$dbh->do("UPDATE song SET present=0 WHERE id=$id");
	} else {
		print "$file: <b>$!</b>\n";
	}
	printftr;
}
elsif($cmd eq 'download') {
	$args{'id'} =~ /(\d+)/;
	my $id = $1;
	my ($file) = $dbh->selectrow_array("SELECT filename FROM song WHERE id=$id")
		or die "id $id not found in database\n";

	open F, $file or die "$file: $!\n";
	print $q->header(-type=>'application/octet-stream', -Content_length=>(-s F));
	while(read F, $_, 4096) { print; }
	close F;
}
elsif($cmd eq 'lists') {
        printhtmlhdr;
	printhdr($allstyle);
	print_lists($dbh);
	printftr;
}
else {
	printhtmlhdr;
	print "oei: $cmd\n";
}

untie %session;
$dbh->disconnect();

