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
 <frame name=playlist src="$self?cmd=playlist&t=$t" marginheight="0">
 <frameset cols="$framewidths" frameborder=no>
  <frame name=artistlist src="$self?cmd=artistlist&t=$t" marginheight="0">
  <frame name=albumlist src="$self?cmd=albumlist&t=$t" marginheight="0">
  <frame name=songlist src="$self?cmd=songlist&t=$t" marginheight="0">
 </frameset>
</frameset>
<body bgcolor=white>
</body>
</html>
EOF
}

sub print_az_table {
	print <<EOF;
<table cellpadding=0 cellspacing=0><tr><td id=az>
<a id=a href="$self?cmd=playlist&t=$t" target=playlist>Refresh</a>&nbsp;&nbsp;
EOF
	$_ = encode("^[^a-zA-Z]");
	print qq|<a id=a href="$self?cmd=artistlist&a=$_&t=$t">0-9</a>&nbsp;|;
	foreach('A'..'Z') {
		my $e = encode("^$_");
		print qq|<a id=a href="$self?cmd=artistlist&a=$e&t=$t">$_</a>&nbsp;|;
	}
	print <<EOF;
</td>
<td id=az>
 <form id=search action="$self" method=get target=artistlist>
  <input type=hidden name=cmd value=artistlist>
   Artist: <input type=text size=5 name=a>
 </form>
</td>
<td id=az>
 <form id=search action="$self" method=get target=albumlist>
 <input type=hidden name=cmd value=albumlist>
   Album: <input type=text size=5 name=s>
 </form>
</td>
<td id=az>
 <form id=search action="$self" method=get target=songlist>
  <input type=hidden name=cmd value=songlist>
   Title: <input type=text size=5 name=t>
 </form>
</td>
<td id=az>&nbsp;&nbsp;
<a id=a target=_blank href="$self?cmd=maint&t=$t" target=playlist>Maintenance</a>
</td>
<td id=az>&nbsp;&nbsp;
<a id=a href="$self?cmd=shuffle&t=$t" target=playlist>Shuffle queue</a>
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
	return sprintf <<EOF, $_[0], $_[1], $_[2], $_[3], $ar, $_[4]->{artist}, $al, $ar, $_[4]->{album}, $tr, $_[4]->{title}, $l, $e;
 <tr>
  <td><a id=a href="%s" target=playlist>%s</a> <a id=a href="%s" target=playlist>%s</a></td>
  <td><a href="$self?cmd=albumlist&a=%s&t=$t" target=albumlist>%s</a></td>
  <td><a href="$self?cmd=songlist&s=%s&a=%s&t=$t" target=songlist>%s</a></td>
  <td>%s&nbsp;</td>
  <td>%s</td>
  <td>%s</td>
  <td>%s</td>
 </tr>
EOF
}

sub print_playlist_table($$) {
	my ($dbh, $nowplaying) = @_;
	my $output;
	my $delall;

	if(!$nowplaying) {
		local *F;
		if(open F, $statusfile) {
			$nowplaying = <F>;
			close F;
		}
	}
	if($nowplaying) {
		my $query =  "SELECT title,artist,album,id,track,length,encoding" .
			" FROM songs" .
			" WHERE id = $nowplaying";
		my $sth = $dbh->prepare($query);
		my $rv = $sth->execute;
		if($_ = $sth->fetchrow_hashref) {
			$output .= get_playlist_table_entry
				"$self?cmd=kill&t=$t", $killtext, "", "", $_;
		}
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
			"$self?cmd=del&id=$_->{id}&t=$t", $deltext,
			"$self?cmd=up&id=$_->{id}&t=$t", $uptext,
			$_;
	}
	if(@ids) {
		$delall = sprintf <<EOF, join(",", @ids);
<a id=a href="$self?cmd=del&id=%s" target=playlist>$delalltext</a>
EOF
	}
	print <<EOF;
<table border=0 cellspacing=0>
 <tr>
  <th width=$width_left>$delall</th>
  <th width=$width_artist>Artist</th>
  <th width=$width_album>Album</th>
  <th width=$width_num>#</th>
  <th width=$width_song>Song</th>
  <th width=$width_time>Time&nbsp;</th>
  <th width=$width_enc>Encoding</th>
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
  <th width=80%>Artist</th>
  <th width=20%>#&nbsp;Songs</th>
 </tr>
EOF

	my $query = "SELECT DISTINCT artist, count(*)" .
			" FROM songs WHERE artist REGEXP ?".
			" GROUP BY artist ORDER BY artist";
	my $sth = $dbh->prepare($query);
	my $rv = $sth->execute($val);
	while(@_ = $sth->fetchrow_array) {
		printf <<EOF, encode("^$_[0]\$"), $_[0], $_[1];
<tr>
 <td><a id=a href="$self?cmd=albumlist&a=%s&s=&t=$t">%s</a>&nbsp;&nbsp;</td>
 <td>%s</td>
</tr>
EOF
	}

	print <<EOF;
</table>
EOF
}

sub print_albumlist_table($@) {
	my ($dbh, $qart, $qalb) = @_;

	print <<EOF;
<table border=0 cellspacing=0>
<caption>Artist: $val[0], Album: $val[1]</caption>
 <tr>
  <th width=99%>Album</th>
  <th width=1%>#&nbsp;Songs</th>
 </tr>
EOF

	my $query = "SELECT DISTINCT album, artist, count(*)" .
			" FROM songs WHERE artist REGEXP ? AND album REGEXP ?".
			" GROUP BY album,artist ORDER BY album";
	my $sth = $dbh->prepare($query);
	my $rv = $sth->execute($qart, $qalb);
	while(@_ = $sth->fetchrow_array) {
		my ($al, $ar, $count) = @_;
		my $newqal = $al;
		$al = "?" unless $al;
		if($qart eq '^') { $al .= " [$ar]"; }
		printf <<EOF, encode("^$ar\$"), encode("^$newqal\$"), $al, $count;
<tr>
 <td><a id=a href="$self?cmd=songlist&a=%s&s=%s&t=$t">%s</a>&nbsp;&nbsp;</td>
 <td>%s</td>
</tr>
EOF
	}

	print <<EOF;
</table>
EOF
}

sub print_songlist_table($@) {
	my ($dbh, @val) = @_;
	my ($output, $addall, $delete);

	my $query = "SELECT artist,title,id,track,length,encoding".
			" FROM songs" .
			" WHERE artist REGEXP ? AND album REGEXP ? AND title REGEXP ?".
			" ORDER BY track,title";
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
		my $esca = $_->{artist};
		$esca =~ s/(['"<>])/sprintf "\\x%02x", ord($1)/ge;
		$output .= sprintf <<EOF, $tr, $_->{id}, $esca, $_->{title}, $l, $e;
 <tr>
  <td>%s&nbsp;</td>
  <td><a id=a href="$self?cmd=add&id=%d&t=$t"
       onMouseOver="window.status='%s';return true"
       onMouseOut="window.status=''; return true"
      >%s</a></td>
  <td>%s</td>
  <td>%s</td>
 </tr>
EOF
	}
	if(@ids) {
	$addall = sprintf <<EOF, join(",", @ids);
   <a id=a href="$self?cmd=add&id=%s&t=$t">$addalltext</a>
EOF
	$delete = sprintf <<EOF, join(",", @ids);
   <a id=a href="$self?cmd=delfiles&id=%s&t=$t" target=songlist>$delfiletext</a>
EOF
	}

	print <<EOF;
<table border=0 cellspacing=0>
<caption>Artist: $val[0], Album: $val[1]</caption>
<tr>
 <td colspan=4>$addall &nbsp;&nbsp; $delete</td>
</tr>
 <tr>
  <th width=1%>#</th>
  <th>Song</th>
  <th width=1%>Time&nbsp;</th>
  <th width=1%>Encoding</th>
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

my $t = time;
	
my $cmd = $args{'cmd'};

my $r = $refreshtime;
my $nowplaying;

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
<META HTTP-EQUIV="Refresh" CONTENT="$r;URL=$self?cmd=playlist&s=$args{'s'}&t=$t">
EOF
	printhdr($plstyle);
	print "<base target=artistlist>\n";
	print $topwindow_title;
	print_az_table();
	print_playlist_table($dbh, $nowplaying);
	printftr;
}
elsif($cmd eq 'artistlist') {
	printhtmlhdr;
	printhdr($alstyle);
	print "<base target=albumlist>\n";
	if($args{'a'}) {
		print_artistlist_table($dbh, $args{'a'});
	}
	printftr;
}
elsif($cmd eq 'albumlist') {
	printhtmlhdr;
	printhdr($abstyle);
	print "<base target=songlist>\n";
	if($args{'a'} || $args{'s'}) {
		print_albumlist_table($dbh, $args{'a'} || "^", $args{'s'} || "^");
	}
	printftr;
}
elsif($cmd eq 'songlist') {
	printhtmlhdr;
	printhdr($slstyle);
	print "<base target=playlist>\n";
	if($args{'a'} || $args{'s'} || $args{'t'}) {
		$args{'a'} =~ s/[^-^ _0-9a-z]+/.*/ig;
		$args{'s'} =~ s/[^-^ _0-9a-z]+/.*/ig;
		$args{'t'} =~ s/[^-^ _0-9a-z]+/.*/ig;
		print_songlist_table($dbh, $args{'a'} || "^",
			$args{'s'} || "^", $args{'t'} || "^");
	}
	printftr;
}
elsif($cmd eq 'maint') {
	printhtmlhdr;
	printhdr($slstyle);
	print <<EOF;
<a href="$self?cmd=update">Quick update</a> (leave existing files alone).<br>
<a href="$self?cmd=update&args=-f">Full update</a> (re-enter info for existing files).<br>
EOF
	printftr;
}
elsif($cmd eq 'update') {
	printhtmlhdr;
	printhdr($slstyle);
	print "<pre>\n";
	print `$progdir/soepkiptng_update $args{'args'} 2>/dev/null`;
	print "</pre>\n";
	printftr;
}
elsif($cmd eq 'delfiles') {
	printhtmlhdr;
	printhdr($slstyle);
	print "<table><tr><th>Delete files:</th></tr>\n";
	foreach(split /,/, $args{'id'}) {
		my ($filename) = $dbh->selectrow_array(
			"SELECT filename FROM songs WHERE id=$_"
		);
		$filename =~ m|([^/]*)$|;
		printf <<EOF, encode($filename), $1;
<tr><td><a id=a href="$self?cmd=delfile&file=%s" target=albumlist>%s</a></td></tr>
EOF
	}
	print "</table>\n";
	printftr;
}
elsif($cmd eq 'delfile') {
	printhtmlhdr;
	printhdr($slstyle);
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


