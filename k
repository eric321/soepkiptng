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

use DBI;
use Socket;

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

$ENV{'PATH'} = "$conf{progdir}/bin:$ENV{'PATH'}";
require "$conf{progdir}/soepkiptng.lib";

$dbh = DBI->connect("DBI:$conf{db_type}:$conf{db_name}:$conf{db_host}",
	$conf{db_user}, $conf{db_pass}) or die "can't connect to database";

($song_id) = kill_song();
($t, $a, $al, $tr) = $dbh->selectrow_array(
	"SELECT song.title,artist.name,album.name,song.track" .
	" FROM song,artist,album" .
	" WHERE song.id=$song_id" .
	" AND song.artist_id=artist.id AND song.album_id=album.id"
);
printf "next: %s - %02d. %s [%s]\n", $a, $tr, $t, $al;


