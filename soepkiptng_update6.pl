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


sub uuid_gen() {
	local *F;
	my $buf;
	
	open F, "/dev/urandom" or die "/dev/urandom: $!\n";
	read F, $buf, 16;
	close F;
	
	my @w = unpack("n*", $buf);
	$w[3] &= 0x0fff; $w[3] |= 0x4000;
	$w[4] &= 0x3fff; $w[4] |= 0x8000;

	$buf = pack("n8", @w);
	return $buf;
}

sub uuid_ascii($)
{
	my @w = unpack("n*", $_[0]);
	return sprintf "%04x%04x-%04x-%04x-%04x-%04x%04x%04x", @w;
}


$| = 1;

$dbh = DBI->connect("DBI:$conf{db_type}:$conf{db_name}:$conf{db_host}",
	$conf{db_user}, $conf{db_pass}) or die "can't connect to database";

$ids = $dbh->selectcol_arrayref("SELECT id FROM song WHERE present AND filename LIKE '/%' AND uuid IS NULL");

foreach(@$ids) {
	$uuid = uuid_ascii(uuid_gen);
	$dbh->do("UPDATE song SET uuid=? WHERE id=?", undef, $uuid, $_);
	printf "%s %s\n", $uuid, $_;
}
