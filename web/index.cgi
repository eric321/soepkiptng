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
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.

############################################################################

BEGIN {
	# find program directory
	$_ = $0;
	while(-l) {
		my $l = readlink or die "readlink $_: $!\n";
		if($l =~ m|^/|) { $_ = $l; } else { s|[^/]*$|/$l|; }
	}
	m|(.*)/|;
	(my $progdir = Cwd::abs_path($1)) =~ s|/+[^/]+$||;

	require "$progdir/soepkiptng.lib";
	require "$progdir/soepkiptng_web.lib";
}

############################################################################
# SUBROUTINES

sub get_host($) {
	my ($req) = @_;

	my $host = $req->header_in('X-Forwarded-For')
		|| $req->get_remote_host();
	if($host =~ /^\d+\.\d+\.\d+\.\d+$/) {
		$host = gethostbyaddr(inet_aton($host), AF_INET) || $host;
	}
	return $host;
}

sub printhttphdr() {
	my $r = Apache->request;
	$r->content_type("text/html; charset=ISO-8859-15");
	$r->send_http_header;
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

read_configfile(\%conf);

my $dbh = DBI->connect("DBI:mysql:$conf{db_name}:$conf{db_host}",
	$conf{db_user},$conf{db_pass}, {mysql_client_found_rows =>1 })
	or die "can't connect to database...$!\n";

my $cgiquery = new CGI;

my $r = Apache->request;
$r->no_cache(1);
my $self = $cgiquery->script_name();
handle_request($dbh, $cgiquery, $self, $r);

untie %session;

$dbh->disconnect();
