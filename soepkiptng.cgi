#!/usr/bin/speedy -- -M4 -t600 -r100 -gsoepkiptng

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
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.

############################################################################

use Cwd 'abs_path';
use CGI;
use CGI::SpeedyCGI;
use DBI;
use IO::Socket;
use LWP::UserAgent;
use Socket;

our $progdir;
if(!$progdir) {
	# find program directory
	$_ = $0;
	while(-l) {
		my $l = readlink or die "readlink $_: $!\n";
		if($l =~ m|^/|) { $_ = $l; } else { s|[^/]*$|/$l|; }
	}
	m|(.*)/|;
	$progdir = abs_path($1);
}

require "$progdir/soepkiptng.lib";
require "$progdir/soepkiptng_web.lib";

############################################################################
# SUBROUTINES

sub printhttphdr($) {
	my ($cookies) = @_;

	my $cookie;
	if($cookies) {
		$cookie = $cgiquery->cookie(
			-name=>'sv',
			-value=>$cookies,
			-path=>'/',
			-expires=>'+365d');
	}
	print $cgiquery->header(
		-type=>"text/html; charset=ISO-8859-15",
		-cookie=>$cookie);
}

sub require_write_access() {
	if($conf{write_access_func} &&
		!eval $conf{write_access_func}) {

		printhtmlhdr;
		printhdr($conf{allstyle});
		print "<b>Access Denied.</b>\n";
		printftr;
		exit;
	}
}


############################################################################
# MAIN

my $sp = CGI::SpeedyCGI->new;

our %conf;
%conf or read_configfile(\%conf);

#$conf{db_user} = "soepkiptng_pub";
#$conf{db_pass} = "soepkiptng_pub";

# (re)open database connection if necessary
our $dbh;
if(!$dbh || !$dbh->ping) {
	$dbh = DBI->connect("DBI:mysql:$conf{db_name}:$conf{db_host}",
		$conf{db_user}, $conf{db_pass}, {mysql_client_found_rows => 1 })
		or die "Can't connect to database $conf{db_name}\@$conf{db_host} as user $conf{db_user}\n";
}
$sp->add_shutdown_handler(sub { $dbh and $dbh->logout; });

our $cgiquery = new CGI;

my $req;
$req->{dbh} = $dbh;
$req->{cgiquery} = $cgiquery;
$req->{self} = $cgiquery->script_name();
$req->{host} = $cgiquery->remote_host();
my %cookies = $cgiquery->cookie('sv');
$req->{cookies} = \%cookies;

handle_request($req);
