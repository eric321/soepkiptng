
# $Id$

use Apache::DBI ();
use Apache::Session::MySQL ();
use Apache ();

use CGI (); CGI->compile(':all');
use IO::Socket ();
use Socket ();

$configfile = "/etc/soepkiptng.conf";
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

Apache::DBI->connect_on_init("DBI:$conf{db_type}:$conf{db_name}:$conf{db_host}", $conf{db_user}, $conf{db_pass});

