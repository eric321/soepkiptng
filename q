#!/usr/bin/perl
############################################################################
# soepkiptng (c) copyright 2000 Eric Lammerts <eric@lammerts.org>.
# $Id$
############################################################################
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License, version 2, as 
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# A copy of the GNU General Public License is available on the World Wide Web
# at `http://www.gnu.org/copyleft/gpl.html'.  You can also obtain it by
# writing to the Free Software Foundation, Inc., 59 Temple Place - Suite 330,
# Boston, MA 02111-1307, USA.
############################################################################

# CONFIG

$configfile = "/etc/soepkiptng.conf";

use integer;
use DBI;
use Socket;
use Getopt::Std;

getopts('vn');

eval "use Term::ReadKey;";
if($@) {
	warn "Term::ReadKey not found; assuming 80-column terminal.\n";
	$screen_width = 80;
} else {
	($screen_width) = GetTerminalSize();
}

open F, $configfile or die "$configfile: $!\n";
while(<F>) {
	/^#/ and next;
	s/\s+$//;
	/./ or next;
	if(/^(\w+)\s*=\s*(.*?)\s*$/) {
		$f = $1;
		$conf{$f} = $2;
	} elsif(/^\s+(.*?)\s*$/) {
		# continuation line
		$conf{$f} .= "\n$1";
	} else {
		die "$configfile line $.: invalid format\n";
	}
}
close F;

require "$conf{progdir}/soepkiptng.lib";

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

sub killit($) {
	my ($killid) = @_;
	($song_id) = kill_song('', $killid);
	if(!defined($song_id)) {
		print "not killing (song $killid not playing anymore)\n";
		return undef;
	}
	($t, $a, $al, $tr) = $dbh->selectrow_array(
		"SELECT song.title,artist.name,album.name,song.track" .
		" FROM song,artist,album" .
		" WHERE song.id=$song_id" .
		" AND song.artist_id=artist.id AND song.album_id=album.id"
	);
	printf "next: %s - %02d. %s [%s]\n", $a, $tr, $t, $al;
}

$| = 1;

$dbh = DBI->connect("DBI:$conf{db_type}:$conf{db_name}:$conf{db_host}",
	$conf{db_user}, $conf{db_pass}) or die "can't connect to database";

if($opt_n) {
	open F, $conf{statusfile} or exit;
	$nowplaying = <F>;
	close F;

	$ids = $dbh->selectcol_arrayref("SELECT song_id FROM queue,song ".
		"WHERE queue.song_id=song.id AND song.present");
	my %idsq;
	foreach(@$ids) {
#		warn "q $_\n";
		$idsq{$_} = 1;
	}

	my $sth = $dbh->prepare("SELECT song2.* FROM song AS song1,".
		" song AS song2 WHERE song1.id=$nowplaying AND".
		" song1.artist_id = song2.artist_id AND".
		" song1.album_id = song2.album_id AND".
		" song2.track > song1.track AND".
		" song2.present ORDER BY song2.track");
	$sth->execute;
	while($_ = $sth->fetchrow_hashref) {
#warn "$_->{id} $idsq{$_->{id}}\n";
		next if $idsq{$_->{id}};
		last;
	}

	exit unless $_->{id};

	my $user = (getpwuid $<)[6] || getpwuid $< || "uid $<";
	$user =~ s/,.*//;

	print "Adding next song ($_->{track}, $_->{title}).\n";
	add_song($dbh, $user, $_->{id}) or warn "can't add song.\n";
	exit;
}

$screen_width = 80 if $screen_width == 0; # just in case
$w_a = $screen_width * 25 / 100;
$w_t = $screen_width * 45 / 100;
$w_al = $screen_width - $w_a - $w_t - 7;
$w_a > 0 && $w_t > 0 && $w_al > 0 or die "screen size too small.\n";

if(@ARGV) {
	foreach(@ARGV) {
		$q = '';
		if(s/^-//) { $q = " NOT"; }
		s/^\^// or $_ = "%$_";
		s/\$$// or $_ .= "%";

		if($0 =~ /qa$/) {
			$q .= " artist.name LIKE ?";
			push @a, $_;
		}
		elsif($0 =~ /qt$/) {
			$q .= " song.title LIKE ?";
			push @a, $_;
		}
		else {
			$q .= " (song.title LIKE ? OR artist.name LIKE ? OR album.name LIKE ?)";
			push @a, $_, $_, $_;
		}
		push @q, $q;
	}
	$q = "SELECT title,artist.name,album.name,song.id,track,filename,length,encoding" .
	     " FROM song,artist,album" .
	     " WHERE song.artist_id=artist.id AND song.album_id=album.id" .
	     " AND present AND " . join(" AND ", @q) .
	     " ORDER BY artist.name,album.name,song.track,song.title";
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
		$opt_v and printf STDERR "%d:%02d %s %s\n", $q[6] / 60, $q[6] % 60,
			$q[7], $q[5];
		$id[$i] = $q[3];
		$i++;
	}
	exit if $i == 1;
	print STDERR "\nAdd (a=all): ";
	$_ = <STDIN>;
	exit unless /\S/;

	my $user = (getpwuid $<)[6] || getpwuid $< || "uid $<";
	$user =~ s/,.*//;
	if(/^a/i) {
		for($n = 1; $n < $i; $n++) {
			add_song($dbh, $user, $id[$n]) or warn "can't add song.\n";
		}
	} else {
		foreach(splitrange($_, $i)) {
			add_song($dbh, $user, $id[$_]) or warn "can't add song.\n"
				if $id[$_];
		}
	}
}

printf "\n    %-${w_a}s %-${w_t}s %-${w_al}s\n    %s %s %s\n",
	'Artist', 'Song', 'Album', '-'x$w_a, '-'x$w_t, '-'x$w_al;

$i = 1;
if($_ = get_nowplaying($dbh)) {
	printf "1.* %-${w_a}.${w_a}s %-${w_t}.${w_t}s %-${w_al}.${w_al}s\n",
		$_->{artist}, $_->{title}, albumtrack($_->{album}, $_->{track});
	if($_->{id}) { $delid[$i++] = $_->{id}; }
	$nowid = $_->{id};
}

$query = "SELECT song.title,artist.name,album.name,song.id,song.track" .
	" FROM song,artist,album,queue" .
	" WHERE song.id=queue.song_id" .
	" AND song.artist_id=artist.id AND song.album_id=album.id" .
	" ORDER BY queue.song_order";
$sth = $dbh->prepare($query);
$rv = $sth->execute;
while(@q = $sth->fetchrow_array) {
	printf "%-3s %-${w_a}.${w_a}s %-${w_t}.${w_t}s %-${w_al}.${w_al}s\n",
		"$i.", $q[1], $q[0], albumtrack($q[2], $q[4]);
	$delid[$i] = $q[3];
	$i++;
}

print STDERR "\nDelete (a=all): ";
$_ = <STDIN>;
exit unless /\S/;
if(/^S/) {
	shuffle_queue($dbh);
} elsif(/^a/i) {
	$sth = $dbh->prepare("DELETE FROM queue");
	$sth->execute();
	killit($nowid);
} else {
	foreach(splitrange($_, $i)) {
		if($_ == 1) { killit($nowid); }
		else { del_song($dbh, $delid[$_]) if $delid[$_]; }
	}
}

$sth->finish;
$dbh->disconnect;

