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

sub print_az_table {
	print <<EOF;
<table cellpadding=0 cellspacing=0><tr><td id=az>
<a id=a href="$self?cmd=playlist" target=tframe>Refresh</a>&nbsp;&nbsp;
EOF
	$_ = encode("^[^a-zA-Z]");
	print qq|<a id=a href="$self?cmd=artistlist&a=$_" target=bframe>0-9</a>&nbsp;|;
	foreach('A'..'Z') {
		my $e = encode("^$_");
		print qq|<a id=a href="$self?cmd=artistlist&a=$e" target=bframe>$_</a>&nbsp;|;
	}
	print <<EOF;
</td>
<td id=az>
 <form id=search action="$self" method=get target=bframe>
  <input type=hidden name=cmd value=artistlist>
   Artist: <input type=text size=5 name=a style="$searchformstyle">
 </form>
</td>
<td id=az>
 <form id=search action="$self" method=get target=bframe>
 <input type=hidden name=cmd value=alllist><input type=hidden name=f value="album">
   Album: <input type=text size=5 name=v style="$searchformstyle">
 </form>
</td>
<td id=az>
 <form id=search action="$self" method=get target=bframe>
 <input type=hidden name=cmd value=alllist><input type=hidden name=f value="title">
   Title: <input type=text size=5 name=v style="$searchformstyle">
 </form>
</td>
<td id=az>&nbsp;&nbsp;
<a id=a target=_blank href="$self?cmd=maint" target=tframe>Maintenance</a>
</td>
<td id=az>&nbsp;&nbsp;
<a id=a href="$self?cmd=shuffle" target=tframe>Shuffle</a>
</td>
<td id=az>&nbsp;&nbsp;
<a id=a href="$self?cmd=recent&num=100" target=bframe>Recent</a>
</td>
</tr></table>
EOF
}


sub get_playlist_table_entry($$$$$) {
	my $ar = $_[4]->{artist};
#	$ar =~ s/\W+/.*/g;
	$ar = encode("^$ar\$");

	my $al = $_[4]->{album};
#	$al =~ s/\W+/.*/g;
	$al = encode("^$al\$");

	my $l = sprintf "%d:%02d", $_[4]->{length} / 60, $_[4]->{length} % 60;
	my $e = $_[4]->{encoding};
	$e =~ s/ /&nbsp;/g;
	my $tr = $_[4]->{track} || "";
	$tr .= "." if $tr;
	return sprintf <<EOF, $_[0], $_[1], $_[2], $_[3], $ar, $_[4]->{artist}, $al, $_[4]->{album}, $tr, $_[4]->{title}, $l, $e;
 <tr>
  <td $td_left>&nbsp;<a id=a href="%s" target=tframe>%s</a> <a id=a href="%s" target=tframe>%s</a>&nbsp;</td>
  <td $td_artist>&nbsp;<a href="$self?cmd=alllist&f=artist&v=%s" target=bframe>%s</a>&nbsp;</td>
  <td $td_album>&nbsp;<a href="$self?cmd=alllist&f=album&v=%s" target=bframe>%s</a>&nbsp;</td>
  <td $td_track>&nbsp;%s&nbsp;</td>
  <td $td_song>&nbsp;%s&nbsp;</td>
  <td $td_time>&nbsp;%s&nbsp;</td>
  <td $td_enc>&nbsp;%s&nbsp;</td>
 </tr>
EOF
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
		my $query =  "SELECT title,artist,album,id,track,length,encoding" .
			" FROM songs" .
			" WHERE id = $nowplaying";
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

	$query =  "SELECT songs.title,songs.artist,songs.album,songs.id,songs.track,songs.length,songs.encoding" .
		" FROM songs,queue" .
		" WHERE songs.id = queue.song_id ORDER BY queue.song_order";
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
<a id=a href="$self?cmd=del&id=%s" target=tframe>$delalltext</a>
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
 </tr>
$output
</table>
EOF
}

sub print_artistlist_table($$) {
	my ($dbh, $val) = @_;

	print <<EOF;
<table border=0 cellspacing=0>
<caption>Artist: $val</caption>
 <tr>
  <th>Artist</th>
  <th>#&nbsp;Albums</th>
 </tr>
EOF

	my $query = "SELECT DISTINCT artist, album, count(*)" .
			" FROM songs WHERE artist REGEXP ?".
			" GROUP BY artist,album ORDER BY artist,album";
	my $sth = $dbh->prepare($query);
	my $rv = $sth->execute($val);
	my ($a, $al, $c);
	my @artists;
	my %al;
	while(($a, $al, $c) = $sth->fetchrow_array) {
		$al{$a} or push @artists, $a;
		$al{$a} .= sprintf(<<EOF, encode($al || '^$'), $al || "?", $c);
<a id=a href="$self?cmd=alllist&f=album&v=%s">%s (%d)</a>&nbsp;&nbsp;
EOF
	}
	foreach(@artists) {
		$al{$_} =~ s/, $//;
		printf <<EOF, encode("^$_\$"), $_, $al{$_};
<tr>
 <td><a id=a href="$self?cmd=alllist&f=artist&v=%s">%s</a></td>
 <td>%s</td>
</tr>
EOF
	}
	print <<EOF;
</table>
EOF
}

sub print_alllist_table($@) {
	my ($dbh, $query, @val) = @_;
	my ($output, $addall, $delete);

	my $sth = $dbh->prepare($query);
	my $rv = $sth->execute(@val);
	my @ids;
	while($_ = $sth->fetchrow_hashref) {
		push @ids, $_->{id};
		my $l = sprintf "%d:%02d", $_->{length} / 60, $_->{length} % 60;
		my $e = $_->{encoding};
		$e =~ s/ /&nbsp;/g;
		my $tr = $_->{track} || "";
		$tr .= "." if $tr;
		$output .= sprintf <<EOF, $_->{id}, $_->{artist}, $_->{album}, $tr, $_->{title}, $l, $e;
 <tr>
  <td $td_left>&nbsp;<a id=a href="$self?cmd=add&id=%d">$addtext</a>&nbsp;</td>
  <td $td_artist>&nbsp;%s&nbsp;</td>
  <td $td_album>&nbsp;%s&nbsp;</td>
  <td $td_track>&nbsp;%s&nbsp;</td>
  <td $td_song>&nbsp;%s&nbsp;</td>
  <td $td_time>&nbsp;%s&nbsp;</td>
  <td $td_enc>&nbsp;%s&nbsp;</td>
 </tr>
EOF
	}
	if(@ids) {
	$addall = sprintf <<EOF, join(",", @ids);
   <a id=a href="$self?cmd=add&id=%s">$addalltext</a>
EOF
	$delete = sprintf <<EOF, join(",", @ids);
   <a id=a href="$self?cmd=delfiles&id=%s" target=bframe>$delfiletext</a>
EOF
	}

	print <<EOF;
<table border=0 cellspacing=0>
<caption>Artist: $val[0], Album: $val[1]</caption>
<tr>
 <td colspan=4>$delete</td>
</tr>
 <tr>
  <th $th_left>&nbsp;$addall&nbsp;</th>
  <th $th_artist>&nbsp;Artist&nbsp;</th>
  <th $th_album>&nbsp;Album&nbsp;</th>
  <th $th_track>&nbsp;#&nbsp;</th>
  <th $th_song>&nbsp;Song&nbsp;</th>
  <th $th_time>&nbsp;Time&nbsp;</th>
  <th $th_enc>&nbsp;Encoding&nbsp;</th>
 </tr>
$output
</table>
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
$_[0]
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


############################################################################
# MAIN

my $q = new CGI;
$self = $q->url(-relative=>1);
my %args;
foreach($q->param) { $args{$_} = $q->param($_); }

my $dbh = DBI->connect("DBI:mysql:$db_name:$db_host",$db_user,$db_pass, {mysql_client_found_rows =>1 })
	or die "can't connect to database...$!\n";

my $cmd = $args{'cmd'};

my $r = $refreshtime;
my $nowplaying;

if($cmd eq 'empty') {
	printhtmlhdr;
	print "<body $body></body>\n";
	exit;
}

if($cmd eq 'add') {
	add_song($dbh, split(/,/, $args{'id'}));
	$cmd = 'playlist';
}
elsif($cmd eq 'del') {
	del_song($dbh, split(/,/, $args{'id'}));
	$cmd = 'playlist';
}
elsif($cmd eq 'up') {
	foreach(reverse split /,/, $args{'id'}) { move_song_to_top($dbh, $_); }
	$cmd = 'playlist';
}
elsif($cmd eq 'kill') {
	($nowplaying) = kill_song();
	$cmd = 'playlist';
#not needed anymore because the cgi waits until the status file has been updated
#	$r = $refreshtime_kill;
}
elsif($cmd eq 'shuffle') {
	shuffle_queue($dbh);
	$cmd = 'playlist';
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
	print_az_table();
	print_playlist_table($dbh, $nowplaying);
	printftr;
}
elsif($cmd eq 'artistlist') {
	printhtmlhdr;
	printhdr($artiststyle);
	print "<base target=bframe>\n";
	print_artistlist_table($dbh, $args{'a'});
	printftr;
}
elsif($cmd eq 'alllist') {
	printhtmlhdr;
	printhdr($allstyle);
	print "<base target=tframe>\n";
	$args{'f'} =~ /^\w*$/ or die;
	my $v = $args{'v'};
	$v =~ s/[^-^\$ _0-9a-z]+/.*/ig;
	print_alllist_table($dbh, 
		"SELECT * FROM songs WHERE $args{'f'} REGEXP ?" .
		" ORDER BY $args{'f'},album,track,artist,title", $v);
	printftr;
}
elsif($cmd eq 'recent') {
	printhtmlhdr;
	printhdr($allstyle);
	print "<base target=tframe>\n";
	print_alllist_table($dbh, 
		"SELECT * FROM songs ORDER BY time_added DESC LIMIT ?",
		(0 + $args{'num'}) || 40);
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
elsif($cmd eq 'delfiles') {
	printhtmlhdr;
	printhdr($allstyle);
	print "<table><tr><th>Delete files:</th></tr>\n";
	foreach(split /,/, $args{'id'}) {
		my ($filename) = $dbh->selectrow_array(
			"SELECT filename FROM songs WHERE id=$_"
		);
		$filename =~ m|([^/]*)$|;
		printf <<EOF, encode($filename), $1;
<tr><td><a id=a href="$self?cmd=delfile&file=%s" target=bframe>%s</a></td></tr>
EOF
	}
	print "</table>\n";
	printftr;
}
elsif($cmd eq 'delfile') {
	printhtmlhdr;
	printhdr($allstyle);
	print "<table></tr><td>";
	if(unlink $args{'file'}) {
		print "$args{'file'} deleted from disk.\n";
		$dbh->do("DELETE FROM songs WHERE filename like ?", undef, $args{'file'});
	} else {
		print "$args{'file'}: <b>$!</b>\n";
	}
	print "</td></tr></table>\n";
	printftr;
}
else {
	printhtmlhdr;
	print "oei\n";
}
$dbh->disconnect();

