#!/usr/bin/perl

$configfile = "/etc/soepkiptng.conf";

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

use integer;
use Term::ReadKey;
use DBI;

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

sub albumtrack($$) {
	my ($album, $track) = @_;

	if($track) {
		my $nr = "[$track]";
		$album = substr($album, 0, $w_al - length($nr));
		if(length($album) != $w_al - length($nr)) { $album .= " "; }
		$album .= $nr;
	} else {
		$album = substr($album, 0, $w_al);
	}
	$album;
};

sub splitrange($$) {
	my ($val, $max) = @_;
	my @ret;
	
	$val =~ s/\b\s+\b/,/g;
	s/\s//g;
	foreach(split /,/, $val) {
		if(/(\d*)-(\d*)/) {
			my ($b, $e, $i);
			$b = $1;
			$e = $2 || $max;
			for($i = $b; $i <= $e; $i++) {
				push @ret, $i;
			}
		} else {
			push @ret, $_;
		}
	}
	@ret;
}

$| = 1;

$dbh = DBI->connect("DBI:$db_type:$db_name:$db_host", $db_user, $db_pass)
	or die "can't connect to database";

($wchar, $hchar, $wpixels, $hpixels) = GetTerminalSize();
$wchar = 80 if $wchar == 0; # just in case
$w_a = $wchar * 25 / 100;
$w_t = $wchar * 45 / 100;
$w_al = $wchar - $w_a - $w_t - 7;
$w_a > 0 && $w_t > 0 && $w_al > 0 or die "screen size too small.\n";

if(@ARGV) {
	foreach(@ARGV) {
		$q = '';
		if(s/^-//) { $q = " NOT"; }
		s/^\^// or $_ = "%$_";
		s/\$$// or $_ .= "%";

		if($0 =~ /qa$/) {
			$q .= " artist LIKE ?";
			push @a, $_;
		}
		elsif($0 =~ /qt$/) {
			$q .= " title LIKE ?";
			push @a, $_;
		}
		else {
			$q .= " (title LIKE ? OR artist LIKE ? OR album LIKE ?)";
			push @a, $_, $_, $_;
		}
		push @q, $q;
	}
	$q = "SELECT title,artist,album,id,track FROM songs WHERE" . join(" AND ", @q) .
		" ORDER BY artist,album,track,title";
#warn $q;
	$sth = $dbh->prepare($q);
	$sth->execute(@a);

	$head = sprintf("\n    %-${w_a}s %-${w_t}s %-${w_al}s\n    %s %s %s\n",
		'Artist', 'Song', 'Album', '-'x$w_a, '-'x$w_t, '-'x$w_al);

	$i = 1;
	while(@q = $sth->fetchrow_array) {
		print STDERR $head;
		$head = '';
		printf STDERR "%-3s %-${w_a}.${w_a}s %-${w_t}.${w_t}s %-${w_al}.${w_al}s\n",
			"$i.", $q[1], $q[0], albumtrack($q[2], $q[4]);
		$id[$i] = $q[3];
		$i++;
	}
	exit if $i == 1;
	$sth = $dbh->prepare("INSERT INTO queue (song_id) VALUES (?)");
	print STDERR "\nAdd (a=all): ";
	$_ = <STDIN>;
	exit unless /\S/;
	if(/^a/i) {
		for($n = 1; $n < $i; $n++) {
			$sth->execute($id[$n]);
		}
	} else {
		foreach(splitrange($_, $i)) {
			$sth->execute($id[$_]) if $id[$_];
		}
	}
}

printf "\n    %-${w_a}s %-${w_t}s %-${w_al}s\n    %s %s %s\n",
	'Artist', 'Song', 'Album', '-'x$w_a, '-'x$w_t, '-'x$w_al;

$i = 1;
if(open F, $statusfile) {
	$nowplaying = <F>;
	close F;

	my $query =  "SELECT title,artist,album,id,track" .
		" FROM songs" .
		" WHERE id = $nowplaying";
	my $sth = $dbh->prepare($query);
	my $rv = $sth->execute;
	if($now_playing = $sth->fetchrow_hashref) {
		printf "1.* %-${w_a}.${w_a}s %-${w_t}.${w_t}s %-${w_al}.${w_al}s\n",
			$now_playing->{artist}, $now_playing->{title},
			albumtrack($now_playing->{album}, $now_playing->{track});
		$delid[1] = $now_playing->{id};
		$i++;
	}
}

$query =  "SELECT songs.title,songs.artist,songs.album,songs.id,songs.track FROM songs,queue" .
	" WHERE songs.id = queue.song_id ORDER BY queue.id";
$sth = $dbh->prepare($query);
$rv = $sth->execute;
while(@q = $sth->fetchrow_array) {
	next if $q[3] == $nowplaying;
	printf "%-3s %-${w_a}.${w_a}s %-${w_t}.${w_t}s %-${w_al}.${w_al}s\n",
		"$i.", $q[1], $q[0], albumtrack($q[2], $q[4]);
	$delid[$i] = $q[3];
	$i++;
}

print STDERR "\nDelete (a=all): ";
$_ = <STDIN>;
exit unless /\S/;
if(/^a/i) {
	$sth = $dbh->prepare("DELETE FROM queue");
	$sth->execute();
	kill_song();
} else {
	$sth = $dbh->prepare("DELETE FROM queue WHERE song_id=?");
	foreach(splitrange($_, $i)) {
		if($_ == 1) { kill_song(); }
		else { $sth->execute($delid[$_]) if $delid[$_]; }
	}
}

$sth->finish;
$dbh->disconnect;

