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

getopts('c:');

read_configfile(\%conf, $opt_c);

$dbh = connect_to_db(\%conf);

$files = $dbh->selectcol_arrayref("SELECT filename FROM song WHERE present AND filesize IS NULL AND filename LIKE '/%'");
$num = 0;
foreach(@$files) {
	defined($size = -s $_) or next;
	$dbh->do("UPDATE song SET filesize=? WHERE filename=?", undef, $size, $_)
		or die "can't do sql command: " . $dbh->errstr . "\n";
	$num++;
}
END {
	print "$num records updated\n";
}
