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

use Cwd 'abs_path';
use DBI;
use Getopt::Std; 
use Socket;

# find program directory
$_ = $0;
while(-l) {
	my $l = readlink or die "readlink $_: $!\n";
	if($l =~ m|^/|) { $_ = $l; } else { s|[^/]*$|/$l|; }
}
m|(.*)/|;
my $progdir = abs_path($1);

require "$progdir/soepkiptng.lib";

getopts('c:');
read_configfile(\%conf, $opt_c);

$ENV{PATH} = "$progdir/bin:$ENV{PATH}";

chop(($song_id, undef, undef, undef, undef, undef, $type,
	$user, $artist, $title, $album, $track, $len, $enc) = kill_song());

printf "next: %s - %02d. %s [%s]\n", $artist, $track, $title, $album;
