#!/usr/bin/perl
############################################################################
# soepkiptng (c) copyright 2000 Eric Lammerts <eric@lammerts.org>.
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

use integer;
use Cwd 'abs_path';
use DBI;
use Socket;
use Getopt::Std;

# find program directory
$_ = $0;
while(-l) {
	my $l = readlink or die "readlink $_: $!\n";
	if($l =~ m|^/|) { $_ = $l; } else { s|[^/]*$|/$l|; }
}
m|(.*)/|;
my $progdir = abs_path($1);

require "$progdir/soepkiptng.lib";

getopts('avnc:gt:');

read_configfile(\%conf, $opt_c);

eval "use Term::ReadKey;";
if($@) {
	warn "Term::ReadKey not found; assuming 80-column terminal.\n";
	$screen_width = 80;
} else {
	if(-t) {
		($screen_width) = GetTerminalSize();
	} else {
		$screen_width = 80;
	}
}

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

$dbh = connect_to_db(\%conf);

if($opt_n) {
	open F, $conf{statusfile} or exit;
	$nowplaying = <F>;
	close F;

	my $user = (getpwuid $<)[6] || getpwuid $< || "uid $<";
	$user =~ s/,.*//;
	my $song = add_song_next($dbh, "queue", $nowplaying, $user)
		or die "No next song.\n";

	print "Adding next song ($song->{track}, $song->{title}).\n";
	exit;
}

$screen_width = 80 if $screen_width == 0; # just in case
$w_a = $screen_width * 25 / 100;
$w_t = $screen_width * 45 / 100;
$w_al = $screen_width - $w_a - $w_t - 7;
$w_a > 0 && $w_t > 0 && $w_al > 0 or die "screen size too small.\n";

if($0 =~ /qr$/ || @ARGV) {
	my @a;
	foreach(@ARGV) {
		$q = '';
		if(s/^-//) { $q = " NOT"; }
		my $a = $_;
		$a =~ s/^\w+=//;
		$a =~ s/^\^// or $a = "%$a";
		$a =~ s/\$$// or $a .= "%";

		if($0 =~ /qa$/ || s/^ar=//) {
			$q .= " (artist.name LIKE ?)";
			push @a, $a;
		}
		if($0 =~ /qa$/ || s/^f=//) {
			$q .= " (song.filename LIKE ?)";
			push @a, $a;
		}
		elsif($0 =~ /ql$/ || s/^al=//) {
			$q .= " (album.name LIKE ?)";
			push @a, $a;
		}
		elsif($0 =~ /qt$/ || s/^t=//) {
			$q .= " (song.title LIKE ?)";
			push @a, $a;
		}
		else {
			$q .= " (song.title LIKE ? OR artist.name LIKE ? OR album.name LIKE ?)";
			push @a, $a, $a, $a;
		}
		push @q, $q;
	}
	if($opt_g) {
		push @q, "track > 0";
	}
	if($opt_t) {
		push @q, "track <= $opt_t";
	}
	if($0 =~ /qr$/) {
		push @q, " last_played=0 AND (unix_timestamp(now()) - unix_timestamp(time_added)) < 7*86400";
	}
	$q = "SELECT title,artist.name as artist,album.name as album,song.id as id,track,filename,length,encoding" .
	     " FROM song,artist,album" .
	     " WHERE song.artist_id=artist.id AND song.album_id=album.id" .
	     " AND present AND filename LIKE '/%' AND " . join(" AND ", @q) .
	     " ORDER BY artist.name,album.name,song.track,song.title";
#warn $q;
	$sth = $dbh->prepare($q);
	$sth->execute(@a);

	$head = sprintf("\n    %-${w_a}s %-${w_t}s %-${w_al}s\n    %s %s %s\n",
		'Artist', 'Song', 'Album', '-'x$w_a, '-'x$w_t, '-'x$w_al);

	$i = 1;
	while($_ = $sth->fetchrow_hashref) {
		if($opt_g) {
			my $f = $_->{filename};
			$f =~ s|//+|/|g;
			$f =~ s|^(.*)/|| or die;
			my $d = $1;
			$d =~ s|^.*/|| or die;
			$f =~ s|\.[^.]+$||;
			$f =~ /([^-\w])/ and die "\nERROR: invalid character ($1) in filename ($f)!\n";
			if(defined($dirname)) {
				$dirname eq $d or die "\nERROR: inconsistent dirname ($dirname, $d)\n";
			} else {
				$dirname = $d;
				$g_output .= ">$dirname\n";
			}
			$_->{title} =~ s/^(\W+)/<$1>/;
			$g_artist = $_->{artist} unless $g_artist;
			$g_album = $_->{album} unless $g_album;
			$g_output .=  "-$_->{track}\n" if $_->{track};
			$g_output .=  "/$f\n";
			$g_output .=  ":$_->{artist}\n" unless $_->{artist} eq $g_artist;
			$g_output .=  "$_->{title}\n";
			next;
		}
		print STDERR $head;
		$head = '';
#		$sep = ($i % 5) == 4? "_":" ";
#		printf STDERR "%-3s$sep%-${w_a}.${w_a}s$sep%-${w_t}.${w_t}s$sep%-${w_al}.${w_al}s\n",
#			"$i.", $_->{artist}, $_->{title}, albumtrack($_->{album}, $_->{track});
		my $s = sprintf "%-3s %-${w_a}.${w_a}s %-${w_t}.${w_t}s %-${w_al}.${w_al}s\n",
			"$i.", $_->{artist}, $_->{title}, albumtrack($_->{album}, $_->{track});
		$s =~ s/ /_/g if $i % 5 == 0;
		print STDERR $s;
		$opt_v and printf STDERR "%d:%02d %s %s\n", $_->{length} / 60, $_->{length} % 60,
			$_->{encoding}, $_->{filename};
		$id[$i] = $_->{id};
		$i++;
	}
	if($opt_g) {
		print "$g_artist-$g_album\n";
		print $g_output;
		exit 0;
	}
	exit 1 if $i == 1;
	if($opt_a) {
		$i == 2 or die "More than 1 hit\n"; 
		$_ = 1;
	} else {
		print STDERR "\nAdd (a=all): ";
		$_ = <STDIN>;
		exit unless /\S/;
	}

	my $user = (getpwuid $<)[6] || getpwuid $< || "uid $<";
	$user =~ s/,.*//;
	if(/^a/i) {
		for($n = 1; $n < $i; $n++) {
			add_song($dbh, "queue", $user, $id[$n]) or warn "can't add song.\n";
		}
	} else {
		foreach(splitrange($_, $i)) {
			add_song($dbh, "queue", $user, $id[$_]) or warn "can't add song.\n"
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

$opt_a and exit;
print STDERR "\nDelete (a=all): ";
$_ = <STDIN>;
exit unless /\S/;
if(/^S/) {
	shuffle_table($dbh, "queue");
} elsif(/^a/i) {
	$sth = $dbh->prepare("DELETE FROM queue");
	$sth->execute();
	killit($nowid);
} else {
	foreach(splitrange($_, $i)) {
		if($_ == 1) { killit($nowid); }
		else { del_song($dbh, "queue", $delid[$_]) if $delid[$_]; }
	}
}

$sth->finish;
$dbh->disconnect;

