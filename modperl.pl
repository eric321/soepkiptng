
# $Id$

use Apache::DBI ();
use Apache::Session::MySQL ();
use Apache ();

use Cwd 'abs_path';
use CGI (); CGI->compile(':all');
use IO::Socket ();
use Socket ();

# find program directory
$_ = $0;
while(-l) {
	my $l = readlink or die "readlink $_: $!\n";
	if($l =~ m|^/|) { $_ = $l; } else { s|[^/]*$|/$l|; }
}
m|(.*)/|;
(my $progdir = abs_path($1)) =~ s|/+[^/]+$||;

require "$progdir/soepkiptng.lib";

read_configfile(\%conf);

Apache::DBI->connect_on_init("DBI:$conf{db_type}:$conf{db_name}:$conf{db_host}", $conf{db_user}, $conf{db_pass});
