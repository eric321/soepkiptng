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
}


############################################################################
# SUBROUTINES

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

sub can_delete($) {
	my ($file) = @_;

	my $dir = $file;
	$dir =~ s|[^/]*$||;
	return 1 if -w $dir;
	return 1 if -k $dir && -w $file;
}

sub ids_encode(@) {
	my $prev = 0;
	my $out = '';
	foreach(@_) {
		if($_ > $prev && $_ - $prev <= 26) {
			$out .= chr(ord('A') - 1 + $_ - $prev);
		} elsif($_ < $prev && $prev - $_ <= 26) {
			$out .= chr(ord('a') - 1 + $prev - $_);
		} else {
			if($_ - $prev >= 0 && substr($out, -1) =~ /\d/) {
				$out .= "+";
			}
			$out .= ($_ - $prev);
		}
		$prev = $_;
	}
	$out =~ s/(([a-z])\2{3,})/"_" . length($1) . $2/egi;
	return $out;
}

sub ids_decode($) {
	my ($str) = @_;
	my $val = 0;
	my @out = ();
	$str =~ s/_(\d+)([a-z])/$2x$1/egi;
	while($str) {
		if($str =~ s/^([a-z])//) {
			$val -= ord($1) - (ord('a') - 1);
		} elsif($str =~ s/^([A-Z])//) {
			$val += ord($1) - (ord('A') - 1);
		} elsif($str =~ s/^([-+ ]?\d+)//) {
			$val += $1;
		} else {
			die "Invalid id encoding: '$str'\n";
		}
		push @out, $val;
	}
	return @out;
}


sub print_frame() {
	print <<EOF;
<html>
<head>
<title>$conf{title}</title>
</head>
<frameset rows="$conf{frameheights}">
 <frame name=tframe src="$self?cmd=playlist" marginheight="$conf{marginheight}">
 <frame name=bframe src="$self?cmd=empty" marginheight="$conf{marginheight}">
</frameset>
<body $conf{body}>
</body>
</html>
EOF
}

sub print_az_table($$) {
	my ($dbh, $session) = @_;
	my ($playlistopts, $editlistopts);

	my $sth = $dbh->prepare("SELECT id,name FROM list ORDER BY name");
	$sth->execute;
	while($_ = $sth->fetchrow_hashref) {
		$playlistopts .= sprintf("   <option value=%d%s>%s\n", $_->{id},
			$_->{id} == $session->{playlist}? " selected":"", $_->{name});
		$editlistopts .= sprintf("   <option value=%d%s>%s\n", $_->{id},
			$_->{id} == $session->{editlist}? " selected":"", $_->{name});
	}

	printf <<EOF, $self;
<table cellpadding=2 cellspacing=0 width=100%><tr><td id=az nowrap>
<a id=az href="%s?cmd=playlist">Refresh</a>&nbsp;&nbsp;
EOF
	foreach('A'..'Z') {
		printf qq|<a id=az href="%s?cmd=%s&artist=%s" target=bframe>%s</a>&nbsp;|,
			$self, $conf{artistlistcmd}, encurl("^$_"), $_;
	}
	printf <<EOF, $self, $conf{artistlistcmd}, encurl("^([^a-zA-Z]|\$)");
<a id=az href="%s?cmd=%s&artist=%s" target=bframe>Other</a>&nbsp;
EOF

	my $sz = $conf{searchformsize} || 10;
	print <<EOF;
</td>
<td id=az nowrap>&nbsp;&nbsp;Search:</td>
<td id=az nowrap>
 <form id=search action="$self" method=get target=bframe>
  <input type=hidden name=cmd value=search>
  <input type=text size=$sz name=sval style="$conf{searchformstyle}">
</td>
<td id=az nowrap>
  <select name=stype style="$conf{searchformstyle}" onChange="form.submit()">
   <option value=any>Any
   <option value=artist>Artist
   <option value=title>Title
   <option value=album>Album
   <option value=filename>Filename
  </select>
  <noscript><input type=submit value="Go"></noscript>
 </form>
</td>
EOF

#<!--
#<td id=az>Play:</td>
#<td id=az>
#  <form id=search action="$self" method=get target=tframe>
#  <select name=list onChange="">
#   <option value="">All
#$playlistopts
#  </select>
#  <input type=hidden name=cmd value=setplaylist>
#  <input type=submit value="Ok">
#  </form>
#</td>
#
#<td id=az>Edit:</td>
#<td id=az>
#  <form id=search action="$self" method=get target=tframe>
#  <select name=list onChange="">
#   <option value="">
#$editlistopts
#  </select>
#  <input type=hidden name=cmd value=seteditlist>
#  <input type=submit value="Ok">
#  </form>
#</td>
#
#<td id=az>&nbsp;&nbsp;
#<a id=a target=bframe href="$self?cmd=lists">Playlists</a>
#</td>
#-->
print <<EOF;
 <td id=az>&nbsp;&nbsp;<a id=az href="$self?cmd=shuffle">Shuffle</a></td>
 <td id=az>&nbsp;&nbsp;<a id=az href="$self?cmd=recent&days=7" target=bframe>Recent</a><a id=az href="$self?cmd=recent&days=7&np=1" target=bframe>*</a></td>
 <td id=az>&nbsp;&nbsp;<a id=az href="$self?cmd=alllist&rand=50" target=bframe>Random</a></td>
 <td id=az>&nbsp;&nbsp;<a id=az href="$self?cmd=alllist&encoding=^Video" target=bframe>Video</a></td>
<!-- <td id=az>&nbsp;&nbsp;<a id=az target=_blank href="$self?cmd=maint">*</a></td>-->
 <td id=az>&nbsp;&nbsp;<a id=az target=bframe href="$self?cmd=shoutcast">Shoutcast</a></td>
 <td id=az width=100%>&nbsp;&nbsp;<a id=az target=bframe href="$self?cmd=sql">SQL</a></td>

</tr></table>
EOF
}

sub table_entry($;$$$$) {
	my ($q, $col1, $title_href, $ids, $extra) = @_;

	return sprintf <<EOF,
 <tr>
  <td %s>&nbsp;%s&nbsp;</td>
  <td %s>&nbsp;%s&nbsp;</td>
  <td %s>&nbsp;%s&nbsp;</td>
  <td %s>&nbsp;%s&nbsp;</td>
  <td %s>&nbsp;%s%s%s&nbsp;</td>
  <td %s>&nbsp;%s&nbsp;</td>
  <td %s>&nbsp;%s&nbsp;</td>
  <td %s> %s</td>
  %s
 </tr>
EOF
		$conf{td_left}, $col1,
		$conf{td_artist},
		$q->{arid}? sprintf(qq|<a id=a href="%s?cmd=alllist&artist_id=%s&cap=%s" target=bframe>%s</a>|,
			$self, $q->{arid}, encurl("Artist: $q->{artist}"), enchtml($q->{artist}))
			: enchtml($q->{artist}),
		$conf{td_album},
		$q->{alid}? sprintf(qq|<a id=a href="%s?cmd=alllist&album_id=%s&cap=%s" target=bframe>%s</a>|,
			$self, $q->{alid}, encurl("Album: $q->{album}"), enchtml($q->{album}))
			: enchtml($q->{album}),
		$conf{td_track}, $q->{track}? "$q->{track}." : "",
		$conf{td_song}, $title_href, enchtml($q->{title}), $title_href? "</a>":"",
		$conf{td_time},
		$q->{length}? sprintf("%d:%02d", $q->{length} / 60, $q->{length} % 60) : "?",
		$conf{td_enc}, enchtml($q->{encoding}, 1),
		$conf{td_edit},
		$ids? sprintf(<<EOF, $self, $q->{id}, $ids, $conf{edit_target} || 'bframe') : "",
<a id=a href="%s?cmd=edit&id=%d&ids=%s" title="Edit" target=%s>*</a>
EOF
		$extra;
}

sub albumlist_entry($) {
	my ($res) = @_; 

	$res->{album} =~ /^(.?)(.*)/;
	return sprintf(qq|<a id=a href="%s?cmd=alllist| .
		qq|&artist_id=%d&album_id=%d&cap=%s"><b>%s</b>%s</a> (%d)|,
		$self, $res->{arid}, $res->{alid},
		encurl("Artist: $res->{artist}; Album: $res->{album}"),
		enchtml($1 || "?"), enchtml($2), $res->{c});
}

sub print_playlist_table($) {
	my ($dbh) = @_;
	my $killline;

	$query =  "SELECT title,artist.name as artist,album.name as album," .
		"song.id as id, track, length, encoding, queue.user as user," .
		"song.artist_id as arid, song.album_id as alid, left(filename,1) as f" .
		" FROM song,queue,artist,album WHERE present" .
		" AND song.artist_id=artist.id AND song.album_id=album.id" .
		" AND song.id = queue.song_id ORDER BY queue.song_order";
	my $sth = $dbh->prepare($query);
	my $rv = $sth->execute;
	my @ids;
	my @records;
	while($_ = $sth->fetchrow_hashref) {
		push @ids, $_->{id};
		push @records, $_;
	}

	if($_ = get_nowplaying($dbh)) {
		if($_->{id} > 0) { unshift @ids, $_->{id}; }

		$killline = table_entry($_,
			sprintf(qq|<a id=a href="%s?cmd=kill&id=%s">%s</a>&nbsp;<a id=a href="%s?cmd=addnext&id=%s">next</a>|,
				$self, $_->{id}, $conf{killtext}, $self, $_->{id}),
			undef,
			($_->{filename} =~ m|^/|)? ids_encode(@ids) : "",
			"<td>&nbsp;" . (($conf{show_user} && $_->{user})? "($_->{user})":"") . "</td>"
		);

		if($conf{title_song}) {
			my $alb = $_->{album};
			if($alb && $_->{track}) { $alb .= "/$_->{track}"; }
			if($alb) { $alb = " [$alb]"; }
			printf <<EOF, enchtml("$_->{artist} - $_->{title}$alb");
<script language="Javascript">
<!--
  parent.document.title="%s";
// -->
</script>
EOF
		}
	}

	my $ids = ids_encode(@ids);
	printf <<EOF,
<table border=0 cellspacing=0>
 <tr>
  <th %s>&nbsp;%s&nbsp;</th>
  <th %s>&nbsp;Artist&nbsp;</th>
  <th %s>&nbsp;Album&nbsp;</th>
  <th %s>&nbsp;#&nbsp;</th>
  <th %s>&nbsp;Song&nbsp;</th>
  <th %s>&nbsp;Time&nbsp;&nbsp;</th>
  <th %s>&nbsp;Encoding&nbsp;</th>
  <th %s>&nbsp;&nbsp;</th>
 </tr>
 <tr><td colspan=7></td></tr>
%s%s</table>
EOF
		$conf{th_left}, @ids? sprintf(qq|<a id=a href="%s?cmd=del&ids=%s">| .
			qq|$conf{delalltext}</a>|, $self, ids_encode(@ids)) : "",
		$conf{th_artist}, $conf{th_album}, $conf{th_track}, $conf{th_song},
		$conf{th_time}, $conf{th_enc}, $conf{th_edit},
		$killline,
		join("", map { table_entry($_, sprintf(
			qq|<a id=a href="%s?cmd=del&ids=%s">%s</a> | .
			qq|<a id=a href="%s?cmd=up&id=%s">%s</a>|,
			$self, $_->{id}, $conf{deltext}, $self, $_->{id}, $conf{uptext}),
			undef, $_->{f} eq '/'? $ids : "",
			($conf{show_user} && $_->{user})? "<td>&nbsp;(".$_->{user}.")</td>":"")
			} @records);
}

sub print_artistlist_table($$$@) {
	my ($dbh, $session, $caption, $query, @val) = @_;

	my $sth = $dbh->prepare($query);
	my $rv = $sth->execute(@val)
		or die "can't do sql command: " . $dbh->errstr;
	my %artistname;
	my %al;
	while($_ = $sth->fetchrow_hashref()) {
		$artistname{$_->{arid}} = $_->{artist};
		$al{$_->{arid}} .= albumlist_entry($_) . ",&nbsp;";
	}


	print "<center id=hdr>$caption</center>\n";
	if(!%artistname) {
		print "No search results.\n";
		return;
	}

	printf <<EOF;
<table border=0 cellspacing=0>
 <tr>
  <th>&nbsp;Artist&nbsp;</th>
  <th>&nbsp;Albums&nbsp;</th>
 </tr>
EOF
	my $res = 0;
	foreach(sort {lc($artistname{$a}) cmp lc($artistname{$b})} keys %artistname) {
		$al{$_} =~ s/,&nbsp;$//;
		printf <<EOF, encurl("Artist: $artistname{$_}"), $artistname{$_}, $al{$_};
<tr>
 <td valign=top>&nbsp;<a id=a href="$self?cmd=alllist&artist_id=$_&cap=%s">%s</a>&nbsp;</td>
 <td valign=top>&nbsp;%s&nbsp;</td>
</tr>
EOF
		$res++;
	}
	print <<EOF;
<tr><td colspan=2>$res search results.</td></tr>
</table>
EOF
}

sub print_albums_row($$$$$) {
	my ($dbh, $baseurl, $argsref, $caption, $artistid) = @_;
	
	my $query = "SELECT seealso.id1 AS id1, seealso.id2 AS id2, ".
		" artist.name AS artist FROM seealso,artist,song WHERE ".
		" (seealso.id2=? AND seealso.id1=artist.id AND ".
		"  seealso.id1=song.artist_id AND song.present) OR".
		" (seealso.id1=? AND seealso.id2=artist.id AND ".
		"  seealso.id2=song.artist_id AND song.present) ".
		" GROUP BY id1, id2, artist ORDER BY artist";
	my $sth = $dbh->prepare($query);
	my $rv = $sth->execute($artistid, $artistid);
	my %seealso;
	my @ids;
	while($_ = $sth->fetchrow_hashref()) {
		if($_->{id1} == $artistid) {
			push @ids, $_->{id2};
			$seealso{$_->{id2}} = $_->{artist};
		} else {
			push @ids, $_->{id1};
			$seealso{$_->{id1}} = $_->{artist};
		}
	}
	$sth->finish;
	if(@ids) {
		print "See Also: ";
		foreach(@ids) {
			print ",&nbsp; " unless $_ == $ids[0];
			print qq|<a id=a href="$self?cmd=seealso&artist_id=$_&cap=|.
				encurl("Artist: $seealso{$_}") . qq|">$seealso{$_}</a>|;
		}
		print ".<br>\n";
	}

	$query = "SELECT DISTINCT binary album.name as album," .
		" binary artist.name as artist, song.random_pref as rp," .
		" count(*) as c, song.artist_id as arid, song.album_id as alid " .
		" FROM song,artist,album WHERE present AND song.artist_id = ?".
		" AND song.artist_id=artist.id AND song.album_id=album.id".
		" AND filename LIKE '/%'".
		" GROUP BY album ORDER BY album";
	$sth = $dbh->prepare($query);
	$rv = $sth->execute($artistid);
	my %al;
	my @alids;
	my $al_len_tot = 0;
	my %al_len;
	my %al_rp;
	while($_ = $sth->fetchrow_hashref()) {
		push @alids, $_->{alid};
		$al{$_->{alid}} = albumlist_entry($_);
		$al_len_tot += $al_len{$_->{alid}} = length($_->{album});
		$al_rp{$_->{alid}} = $_->{rp};
	}
	if($conf{albumlist_length_threshold} == 0 ||
	   $al_len_tot < $conf{albumlist_length_threshold} ||
	   $argsref->{expanded_albumlist}) {
		my $sep = "&nbsp; ";
		if($argsref->{expanded_albumlist}) { $sep = "<br>\n"; }
		printf "Albums:%s%s.\n", $sep, join(",$sep",
			map { $al{$_} } @alids);
	} else {
		my $len_left = $conf{albumlist_length_threshold};
		my %alids_shortlist;
		foreach(sort { $al_rp{$b} <=> $al_rp{$a} || $al_len{$a} <=> $al_len{$b} } @alids) {
			last if $al_len{$_} > $len_left;
			$len_left -= $al_len{$_};
			$alids_shortlist{$_} = 1;
		}
		my @alids2 = grep { $alids_shortlist{$_} } @alids;
		printf "Albums: %s", join(",&nbsp;\n",
			map { $al{$_} } @alids2);
			
		printf <<EOF, $baseurl, $argsref->{cmd}, $#alids - $#alids2;
&nbsp; <a id=a href="%scmd=%s&expanded_albumlist=1">[%d more...].</a>
EOF
	}
}

sub print_alllist_table($$$$@) {
	my ($dbh, $argsref, $session, $caption, $query, $limit, @val) = @_;
	my ($output, $addall);

	print <<EOF;
<center id=hdr>$caption</center>
EOF

	my $sth = $dbh->prepare($query . ($limit? " LIMIT $limit":""));
	my $rv = $sth->execute(@val)
		or die "can't do sql command: " . $dbh->errstr;
	my @ids;
	my %records;
	while($_ = $sth->fetchrow_hashref) {
		$records{$_->{id}} = $_;
		push @ids, $_->{id};
	}
	if(!@ids) {
		print "No search results.\n";
		return;
	}
	my $ids = ids_encode(@ids);

	my $baseurl = "$self?";
	foreach(keys %$argsref) {
		next if $_ eq "cmd";
		next if /^add_/;
		$baseurl .= "$_=" . encurl($argsref->{$_}) . "&";
	}

	my %artistids;
	foreach $id (@ids) {
		$_ = $records{$id};
		$artistids{$_->{arid}}++;
		my $el = $session->{editlist};
		my $listch;
		if($el) {
			if($dbh->do("SELECT entity_id FROM list_contents" .
				" WHERE list_id=? AND (" .
				"  (type=? AND entity_id=?) OR" .
				"  (type=? AND entity_id=?) OR" .
				"  (type=? AND entity_id=?))", undef,
				$el,
				"Song", $_->{id},
				"Artist", $_->{arid},
				"Album", $_->{alid}) < 1) {
				$listch = <<EOF;
&nbsp;<a href="${baseurl}cmd=addtolist&add_list=$el&add_type=song&add_id=$_->{id}" target=bframe>+</a>
EOF
			}
		}

		my $thref = sprintf(qq|<a id=a href="%s?cmd=add&ids=%d" target=tframe>|,
			$self, $_->{id});
		$output .= table_entry($_, "$thref$conf{addtext}</a>", $thref, $ids);
	}

	if(scalar keys %artistids == 1) {
		print_albums_row($dbh, $baseurl, $argsref, $cap, (keys %artistids)[0]);
	}

	print "<table border=0 cellspacing=0>\n";

	if(@ids) {
	$addall = sprintf <<EOF, ids_encode(@ids);
<a id=a href="$self?cmd=add&ids=%s" target=tframe>$conf{addalltext}</a>
EOF
	}

	my %revsort;
	$revsort{$argsref->{sort}} = "r_";

	my $baseurl = "$self?";
	foreach(keys %$argsref) {
		next if $_ eq 'sort';
		$baseurl .= "$_=" . encurl($argsref->{$_}) . "&";
	}

	my $res = $#ids + 1;
	my $limitstr = '';
	$limitstr = " <b>(limit of $limit reached)</b>" if $limit && $res == $limit;
	print <<EOF;
 <tr>
  <th $conf{th_left}>&nbsp;$addall&nbsp;</th>
  <th $conf{th_artist}>&nbsp;<a href="${baseurl}sort=$revsort{artist}artist">Artist</a>&nbsp;</th>
  <th $conf{th_album}>&nbsp;<a href="${baseurl}sort=$revsort{album}album">Album</a>&nbsp;</th>
  <th $conf{th_track}>&nbsp;<a href="${baseurl}sort=$revsort{track}track">#</a>&nbsp;</th>
  <th $conf{th_song}>&nbsp;<a href="${baseurl}sort=$revsort{title}title">Song</a>&nbsp;</th>
  <th $conf{th_time}>&nbsp;<a href="${baseurl}sort=$revsort{length}length">Time</a>&nbsp;</th>
  <th $conf{th_enc}>&nbsp;<a href="${baseurl}sort=$revsort{encoding}encoding">Encoding</a>&nbsp;</th>
  <th $conf{th_edit}>&nbsp;&nbsp;</th>
 </tr>
 <tr><td colspan=7></td></tr>
$output
<tr><td colspan=8>$res search results$limitstr.</td></tr>
</table>
EOF
}

sub print_edit_page($$) {
	my ($dbh, $argsref) = @_;

	my $sth = $dbh->prepare("SELECT artist.name as artist,album.name as album," .
		" reverse(bin(song.sets)) as setbin,song.*," .
		" unix_timestamp(last_played) as lp," .
		" unix_timestamp(time_added) as ta" .
		" FROM song,artist,album WHERE song.id=$argsref->{id}" .
		" AND song.artist_id=artist.id AND song.album_id=album.id");
	$sth->execute();
	$_ = $sth->fetchrow_hashref() or die "id $argsref->{id} not found.\n";

	my $i = 0;
	my @ids = ids_decode($argsref->{ids});
	foreach(@ids) {
		last if $_ == $argsref->{id};
		$i++;
	}
	my $prev = '&nbsp;&nbsp;&nbsp;&nbsp;';
	if($i > 0) {
		$prev = "<input type=submit name=go_$ids[$i-1] value=Prev>";
	} elsif($conf{disabled_buttons}) {
		$prev = "<input type=submit name=go_$ids[0] value=Prev disabled>";
	}

	my $next = $conf{disabled_buttons}? '':'&nbsp;&nbsp;&nbsp;&nbsp;';
	if($i < $#ids) {
		$next = "<input type=submit name=go_$ids[$i+1] value=Next>";
	} elsif($conf{disabled_buttons}) {
		$next = "<input type=submit name=go_$ids[$#ids] value=Next disabled>";
	}

	my $f = $_->{filename};
	$f =~ s|.*/||;
	$f =~ s|\\|_|g;
	$f = encurl($f);
	$_->{filename} =~ m|^(.*)/(.*?)$|;
	my ($dir, $file) = ($1, $2);
	my $dir_ = $dir;
	$dir_ =~ s/ /_/g;

	my $sets = '';
	$sth = $dbh->prepare("SELECT * FROM sets");
	$sth->execute();
	my $i = 0;
	while($set = $sth->fetchrow_hashref()) {
		$sets .= sprintf <<EOF,
<tr>
 <td colspan=2>%s</td>
 <td><input type=checkbox name=sets_%d%s> %s
     <input type=submit name=action_sets_all_%d value=\"Set entire list\"></td>
</tr>
EOF
			$i == 0? "Sets:" : "&nbsp;", $set->{num},
			substr($_->{setbin}, $set->{num}, 1)? " checked" : "",
			$set->{name}, $set->{num};
		$i++;
	}

	printf <<EOF,
<script language="Javascript">
<!--
function verifydelete() {
   return confirm("Are you sure you want to delete this file?");
}
function verifyall() {
   return confirm("Are you sure you want to apply this value to the entire list (%d entries)?");
}
function closethis() {
   window.close(self);
}
// -->
</script>

<form action="%s" method=get>
 <input type=hidden name=id value="%d">
 <input type=hidden name=cmd value=changefile>
 <input type=hidden name=ids value="%s">
<table>
<caption>Edit Song</caption>
  <tr><td valign=bottom colspan=2>Present:</td><td valign=bottom>%s</td></tr>
  <tr><td valign=bottom colspan=2>Artist:</td><td valign=bottom>
     <input type=text size=60 name=artist value="%s">
     <input type=submit name=action_clear_artist value="Clear">
     <input type=submit name=action_fix_artist value="Fix">
     <input type=submit name=action_swapa value="Swap first/last">
     <input type=submit name=action_all_artist value="Set entire list"
      onClick="return verifyall();">
  </td></tr>
  <tr><td valign=bottom colspan=2>Title:</td> <td valign=bottom>
     <input type=text size=60 name=title  value="%s">
     <input type=submit name=action_clear_title value="Clear">
     <input type=submit name=action_fix_title value="Fix">
     <input type=submit name=action_swap value="Swap artist/title">
  </td></tr>
  <tr><td valign=bottom colspan=2>Album:</td> <td valign=bottom>
     <input type=text size=60 name=album  value="%s">
     <input type=submit name=action_clear_album value="Clear">
     <input type=submit name=action_fix_album value="Fix">
     <input type=submit name=action_all_album value="Set entire list"
      onClick="return verifyall();">
  </td></tr>
  <tr><td valign=bottom colspan=2>Track:</td> <td valign=bottom><input type=text size=3 name=track  value="%s" maxlength=3></td></tr>
  <tr><td valign=bottom colspan=2>Time:</td>  <td valign=bottom>%s</td></tr>
  <tr><td valign=bottom colspan=2>Encoding:</td>        <td valign=bottom>%s</td></tr>
  <tr><td valign=bottom colspan=2 nowrap>Time Added:</td><td valign=bottom>%s</td></tr>
  <tr><td valign=bottom colspan=2 nowrap>Last played:</td><td valign=bottom>%s%s
     <input type=submit name=action_setlpall value=\"Set entire list to current time\"></td></tr>
  <tr><td valign=bottom colspan=2 nowrap>Random pref.:</td><td valign=bottom><input type=text size=8 name=random_pref value="%d" maxlength=8>
     <input type=submit name=action_setrpall value="Set entire list." onClick="return verifyall();"></td></tr>
  <tr><td valign=bottom colspan=2>Directory:</td>       <td valign=bottom><a href="%s">%s</a></td></tr>
  <tr><td valign=bottom colspan=2>Filename:</td>        <td valign=bottom><a href="%s">%s</a></td></tr>
  <tr><td valign=bottom colspan=2>Size:</td>            <td valign=bottom>%dk</td></tr>
%s  <tr>
   <td valign=bottom align=center>%s</td>
   <td valign=bottom align=center>%s</td>
   <td valign=bottom>
    <input type=submit value="Update">&nbsp;&nbsp;
<script language="Javascript">
<!--
 document.write('<input type=submit value="Close" onClick="javascript:window.close();">&nbsp;&nbsp;');
// -->
</script>
    %s
   </td>
  </tr>
</table>
</form>
EOF
		$#ids + 1, $self, $argsref->{id}, $argsref->{ids},
		$_->{present}? "Yes" : "No",
		enchtml($_->{artist}),
		enchtml($_->{title}),
		enchtml($_->{album}),
		$_->{track} || "",
		$_->{length}? sprintf("%d:%02d", $_->{length} / 60, $_->{length} % 60) : "?",
		$_->{encoding},
		$_->{ta}? scalar localtime($_->{ta}) : "-",
		$_->{lp}? scalar localtime($_->{lp}) : "-",
		$_->{lp}? " <font size=-1><input type=submit name=action_clearlp value=Reset> " .
			"<input type=submit name=action_clearlpall value=\"Reset entire list\"></font>":"",
		$_->{random_pref},
		"$self?cmd=alllist&sort=artist&filename=" . encurl($dir_), $dir,
		"$self/$f?cmd=download&id=$argsref->{id}", $file,
		((-s $_->{filename}) + 512) / 1024, $sets,
		$prev, $next,
		(can_delete($_->{filename})? qq'<input type=submit ' .
		  qq'name=action_delete value="Delete Song" ' .
		  qq'onclick="return verifydelete();">&nbsp;&nbsp;':'');
}

sub print_shoutcast_page($$) {
	my ($dbh, $args) = @_;

	$args->{name} =~ s/^\s+|\s+$//g;
	$args->{url} =~ s/^\s+|\s+$//g;
	$args->{url} =~ s|^/*(?!http:)(.)|http://$1|;
	foreach(keys %$args) {
		if(/^delete_(\d+)$/) {
			require_write_access;
			$dbh->do("DELETE FROM song WHERE id=?", undef, $1)
				or die "can't do sql command: " . $dbh->errstr;
			delete $args->{editid};
			delete $args->{url};
		}
	}
	if($args->{editid} && $args->{url}) {
		require_write_access;
		if($args->{action_clear_name}) { $args->{name} = ""; }
		$dbh->do("UPDATE song SET title=?,filename=? WHERE id=?",
			undef, $args->{name}, $args->{url}, $args->{editid})
			or die "can't do sql command: " . $dbh->errstr;
	} elsif($args->{url}) {
		require_write_access;
		my $arid = get_id($dbh, "artist", '') or die;
		my $alid = get_id($dbh, "album", '') or die;
		$dbh->do("REPLACE INTO song SET title=?, filename=?, album_id=?, " .
			"artist_id=?, present=1, encoding='Shoutcast', track=0, " .
			"length=0, time_added=NULL", undef,
			$args->{name}, $args->{url}, $alid, $arid) or die;
	}

	printf <<EOF,
<center id=hdr>Shoutcast Radio Channels</center>
<table border=0 cellspacing=0>
 <tr>
  <th %s>&nbsp;<a href="%s?cmd=shoutcast">Refresh</a>&nbsp;</th>
  <th %s>&nbsp;Name&nbsp;</th>
  <th %s>&nbsp;URL&nbsp;</th>
 </tr>
 <tr><td colspan=7></td></tr>
EOF
		$conf{th_left}, $self, $conf{th_artist}, $conf{th_album};

	my $sth = $dbh->prepare("SELECT id,filename,title FROM song WHERE " .
		"filename LIKE 'http:%' ORDER BY title");
	$sth->execute;

	my ($editurl, $editname);
	while($_ = $sth->fetchrow_hashref) {
		my $ref = sprintf(qq|<a id=a href="%s?cmd=add&ids=%d" target=tframe>|,
			$self, $_->{id});
		printf <<EOF,
 <tr>
  <td %s>&nbsp;%s&nbsp;</td>
  <td %s>&nbsp;%s</a>&nbsp;</td>
  <td %s>&nbsp;%s</a>&nbsp;</td>
  <td %s>&nbsp;<a id=a href="%s?cmd=shoutcast&editid=%d" target=bframe>%s</a>&nbsp;</td>
 </tr>
EOF
		$conf{td_left}, "$ref$conf{addtext}</a>",
		$conf{td_artist}, $_->{title},
		$conf{td_album}, $_->{filename},
		$conf{td_track}, $self, $_->{id}, '*';

		if($_->{id} == $args->{editid}) {
			$editurl = $_->{filename};
			$editname = $_->{title};
		}
	}

	printf <<EOF,
</table>
<br>
<hr>
%s server:
<form action="%s" method=get>
 <input type=hidden name=cmd value=shoutcast>
 <input type=hidden name=editid value=%d>
 <table>
 <tr><td>URL:</td><td><input type=text size=60 name=url value="%s"></td></tr>
 <tr><td>Description:</td><td><input type=text size=60 name=name value="%s">
         <input type=submit name=action_clear_name value="Clear"></td></tr>
 <td><td></td></tr>
 <tr><td colspan=2><input type=submit value="%s">%s</td></tr>
 </table>
</form>
<br>
EOF
	$args->{editid}? "Edit" : "Add",
	$self, $args->{editid},
	enchtml($editurl || ""),
	enchtml($editname || ""),
	$args->{editid}? "Update" : "Add",
	$args->{editid}?
		sprintf(qq|&nbsp;<input type=submit name=delete_%d value="Delete">|,
		$args->{editid}) : "";
}

sub print_lists($) {
	my ($dbh) = @_;

	print <<EOF;
<center id=hdr>Playlists</center>
<table border=0 cellspacing=0>
 <tr>
  <th $conf{th_left}>&nbsp</th>
  <th $conf{th_left}>&nbsp;Name&nbsp;</th>
  <th $conf{th_left}>&nbsp;# Songs&nbsp;</th>
 </tr>
 <tr><td colspan=3></td></tr>

EOF
	my $sth = $dbh->prepare("SELECT id,name FROM list ORDER BY name");
	$sth->execute;
	my $d;
	while($d = $sth->fetchrow_hashref) {
		print <<EOF;
 <tr>
  <td $conf{th_left}>&nbsp;<a href="$self?cmd=dellist&id=$d->{id}">del</a>&nbsp;</td>
  <td>&nbsp;<a href="$self?cmd=showlist&id=$d->{id}">$d->{name}</a>&nbsp;</td>
  <td $conf{th_left}>&nbsp;88&nbsp;</td>
 </tr>
EOF
	}
	print <<EOF;
</table>
<p>
<form id=search action="$self" method=get target=bframe>
<input type=text size=20 name=listname>
<input type=hidden name=cmd value=addlist>
<input type=submit value="Add Playlist">
</form>
EOF
}

sub printhtmlhdr() {
	my $r = Apache->request;
	$r->content_type("text/html");
	$r->send_http_header;
	print <<EOF;
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">
EOF
}

sub printhdr($) {
	print <<EOF;
<html>
<head>
<style type="text/css">
<!--
$_[0]
-->
</style>
</head>
<body $conf{body}>
EOF
}

sub printftr() {
	print <<EOF;
</body>
</html>
EOF
}

sub printredirexit($$$$) {
	my ($q, $self, $cmd, $argsref) = @_;
	$argsref->{cmd} = $cmd;
 	print $q->redirect(construct_url($self, $argsref));
	exit;
}

sub add_search_args($$$$@) {
	my ($query, $list, $sort, $val, @fields) = @_;
	my $v;

	# split on space and latin1 'no break space'
	foreach $v (split /[\s\xa0]+/, $val) {
		my $m = "LIKE";
		$$query .= " AND ";
		if($v =~ s/^!//) { $$query .= "NOT "; }
		if($v =~ /^\^/) { $m = "REGEXP"; }
		else { $v = "%$v%"; };
		$$query .= "(" . join(" OR ", map { "$_ $m ?" } @fields) . ")";
		foreach(@fields) { push @$list, $v; }
	}
	$$sort = $fields[0] unless $$sort;
}

sub delete_file($$) {
	my ($dbh, $argsref) = @_;

	require_write_access;

	printhtmlhdr;
	printhdr($conf{allstyle});
	$argsref->{id} =~ /(\d+)/;
	my $id = $1;
	my ($file) = $dbh->selectrow_array("SELECT filename FROM song WHERE id=$id")
		or die "id $id not found in database\n";
	if(unlink $file) {
		print "$file deleted from disk.\n";
		$dbh->do("UPDATE song SET present=0 WHERE id=$id");
	} else {
		print "$file: <b>$!</b>\n";
	}
	printftr;
}

sub get_user($) {
	my ($req) = @_;
	my $user = '';

	my $host = $req->header_in('X-Forwarded-For')
		|| $req->get_remote_host();
	if($host =~ /^\d+\.\d+\.\d+\.\d+$/) {
		$host = gethostbyaddr(inet_aton($host), AF_INET) || $host;
	}
	if($host) {
		$host =~ /^([-a-z0-9]*)/;
		$user = $conf{"user_from_$1"} || $conf{"user_from_$host"} || $host;
	}
	return $user;
}

############################################################################
# MAIN

read_configfile(\%conf);

my $query = new CGI;
my $pathinfo = $query->path_info();
#if($pathinfo =~ s|^/*([.\d]+)/([^/]*)||) {
#	$sessionid = $1;
#	$cmd = $2;
##	$bla = "ja,$pathinfo,$sessionid,$cmd";
#} else {
#	$sessionid = sprintf "%d.%d.%d", $$, time, rand 1e9;
##	$bla = "nee,$pathinfo,$sessionid,$cmd";
#
#	# remove expired entries (>= 1 week old) from session hash
#	my $threshold = time - 7 * 86400;
#	foreach(keys %sessiontime) {
#		if($_ < $threshold) {
#			delete $sessiontime{$_};
#			delete $sessiondata{$_};
#		}
#	}
#}
#$sessiontime{$sessionid} = time;
#$bla = "s=$sessiondata{$sessionid},\$\$=$$";
#$self = $query->script_name() . "/$sessionid/";
$self = $query->script_name();
my %args;
foreach($query->param) { $args{$_} = $query->param($_); }

$SIG{__DIE__} = sub {
	printhtmlhdr;
	print "<p><p>$_[0]\n";
	exit 0;
};

my $dbh = DBI->connect("DBI:mysql:$conf{db_name}:$conf{db_host}",$conf{db_user},$conf{db_pass}, {mysql_client_found_rows =>1 })
	or die "can't connect to database...$!\n";

my $r = Apache->request;
$r->no_cache(1);

my $cmd = $args{cmd};
my $rt = $conf{refreshtime};

if($cmd eq 'empty') {
	printhtmlhdr;
	print "$conf{bframe_start}\n";
	exit;
}

if($cmd eq 'add') {
	add_song($dbh, get_user($r), ids_decode($args{ids}));
 	printredirexit($query, $self, 'playlist', undef);
}
elsif($cmd eq 'del') {
	del_song($dbh, ids_decode($args{ids}));
 	printredirexit($query, $self, 'playlist', undef);
}
elsif($cmd eq 'up') {
	foreach(reverse split /,/, $args{id}) { move_song_to_top($dbh, $_); }
 	printredirexit($query, $self, 'playlist', undef);
}
elsif($cmd eq 'kill') {
	kill_song(get_user($r));
 	printredirexit($query, $self, 'playlist', undef);
}
elsif($cmd eq 'addnext') {
	add_song_next($dbh, $args{id}, get_user($r));
	printredirexit($query, $self, 'playlist', undef);
}
elsif($cmd eq 'setplaylist') {
	$session{playlist} = $args{list};
 	printredirexit($query, $self, 'playlist', undef);
}
elsif($cmd eq 'seteditlist') {
	$session{editlist} = $args{list};
 	printredirexit($query, $self, 'playlist', undef);
}
elsif($cmd eq 'addlist') {
	require_write_access;
	$dbh->do("REPLACE INTO list SET name=?", undef, $args{listname})
		or die;
 	printredirexit($query, $self, 'lists', \%args);
}
elsif($cmd eq 'addtolist') {
	require_write_access;
	$dbh->do("REPLACE INTO list_contents SET type=?, list_id=?, entity_id=?", undef,
		$args{add_type}, $args{add_list}, $args{add_id})
		or die;
	delete $args{add_type};
	delete $args{add_list};
	delete $args{add_id};
 	printredirexit($query, $self, 'alllist', \%args);
}
elsif($cmd eq 'dellist') {
	require_write_access;
	$dbh->do("DELETE FROM list WHERE id=?", undef, $args{id})
		or die;
	$dbh->do("DELETE FROM list_contents WHERE list_id=?", undef, $args{id})
		or die;
 	printredirexit($query, $self, 'lists', \%args);
}
elsif($cmd eq 'shuffle') {
	shuffle_queue($dbh);
 	printredirexit($query, $self, 'playlist', \%args);
	$sessiondata{$sessionid} = 1;
}
elsif($cmd eq 'changefile') {
	my $newid = 0;

	require_write_access;

	if($args{action_delete}) {
		delete_file($dbh, \%args);
		exit;
	}
	if($args{action_clearlp}) {
		$dbh->do("UPDATE song SET last_played=from_unixtime(0) WHERE id=?",
			undef, $args{id})
			or die "can't do sql command: " . $dbh->errstr;
	}
	if($args{action_clearlpall}) {
		foreach(ids_decode($args{ids})) {
			$dbh->do("UPDATE song SET last_played=from_unixtime(0) WHERE id=?",
				undef, $_)
				or die "can't do sql command: " . $dbh->errstr;
		}
	}
	if($args{action_setlpall}) {
		foreach(ids_decode($args{ids})) {
			$dbh->do("UPDATE song SET last_played=NULL WHERE id=?", undef, $_)
				or die "can't do sql command: " . $dbh->errstr;
		}
	}
	if($args{action_setrpall}) {
		foreach(ids_decode($args{ids})) {
			$dbh->do("UPDATE song SET random_pref=? WHERE id=?",
				undef, $args{random_pref}, $_)
				or die "can't do sql command: " . $dbh->errstr;
		}
	}
	elsif($args{action_clear_artist})   { $args{artist} = '' }
	elsif($args{action_clear_title}) { $args{title} = '' }
	elsif($args{action_clear_album}) { $args{album} = '' }
	elsif($args{action_fix_artist}) { $args{artist} = cleanup_name($args{artist}); }
	elsif($args{action_fix_title}) { $args{title} = cleanup_name($args{title}); }
	elsif($args{action_fix_album}) { $args{album} = cleanup_name($args{album}); }
	elsif($args{action_swap}) {
		($args{title}, $args{artist}) = ($args{artist}, $args{title});
	}
	elsif($args{action_swapa}) {
		$args{artist} =~ s/(.*)\s*,\s*(.*)/$2 $1/
			or $args{artist} =~ s/(.*?)\s+(.*)/$2 $1/
	} else {
		foreach(keys %args) {
			if(/^go_(\d+)$/) {
				$newid = $1;
				last;
			}
		}
	}
	my $arid = get_id($dbh, "artist", $args{artist}) or die;
	my $alid = get_id($dbh, "album", $args{album}) or die;

	foreach(keys %args) {
		/^action_sets_all_(\d+)$/ or next;

		if($args{"sets_$1"}) {
			$upd = "sets=(sets | 1 << $1)";
		} else {
			$upd = "sets=(sets & ~(1 << $1))";
		}

		my @ids = ids_decode($args{ids});
		while(@ids) {
			my @ids2 = splice(@ids, 0, 50);
			$dbh->do("UPDATE song SET $upd WHERE " .
				join(" OR ", map { "id=$_" }  @ids2),
				undef, $all_field_arg, @ids2)
				or die "can't do sql command: " . $dbh->errstr;
		}
	}

	my $sets = '0';
	foreach(keys %args) {
		/^sets_(\d+)$/ or next;
		$sets .= " | (1 << $1)";
	}
	

	$dbh->do("UPDATE song SET artist_id=?, title=?, album_id=?, track=?, random_pref=?, sets=($sets) WHERE id=?",
		undef, $arid, $args{title}, $alid, $args{track}, $args{random_pref}, $args{id})
		or die "can't do sql command: " . $dbh->errstr;

	my ($all_field, $all_field_arg);
	if($args{action_all_artist}) {
		$all_field = 'artist';
		$all_field_arg = $arid;
	} elsif($args{action_all_album}) {
		$all_field = 'album';
		$all_field_arg = $alid;
	}
	if($all_field) {
		my @ids = ids_decode($args{ids});

		while(@ids) {
			my @ids2 = splice(@ids, 0, 50);
			$dbh->do("UPDATE song SET ${all_field}_id=? WHERE " .
				join(" OR ", map { "id=$_" }  @ids2),
				undef, $all_field_arg, @ids2)
				or die "can't do sql command: " . $dbh->errstr;
		}
	}

	if($newid) { $args{id} = $newid; }
 	printredirexit($query, $self, 'edit', \%args);
}

if($cmd eq 'search') {
	if(!$args{stype}) {
		printhtmlhdr;
		printhdr($conf{allstyle});
		print "Error: No search type specified.\n";
		printftr;
		exit;
	}
	$args{$args{stype}} = $args{sval};
	if($args{stype} eq 'artist') {
		$cmd = 'artistlist';
	} else {
		$cmd = 'alllist';
	}
}


if($cmd eq '') {
	printhtmlhdr;
	print_frame;
}
elsif($cmd eq 'playlist') {
	printhtmlhdr;
	print <<EOF;
<META HTTP-EQUIV="Refresh" CONTENT="$rt;URL=$self?cmd=playlist&s=$args{s}">
EOF
	printhdr($conf{plstyle});
	print_az_table($dbh, \%session);
	print_playlist_table($dbh);
#	printf "[[%s]]\n", $bla;
	printftr;
}
elsif($cmd eq 'artistlist') {
	printhtmlhdr;
	printhdr($conf{artiststyle});

	my $cap;
	my $s;
	my $q = ("SELECT DISTINCT artist.name as artist, album.name as album," .
		 " count(*) as c, song.artist_id as arid, song.album_id as alid," .
		 " UCASE(album.name) as sort" .
		 " FROM song,artist,album WHERE present AND filename LIKE '/%'");
	my @qargs;

	if($args{artist} =~ /\S/) {
		add_search_args(\$q, \@qargs, \$s, $args{artist}, 'artist.name');
		$cap = "Search Artist: $args{artist}";
	}
	if($args{album} =~ /\S/) {
		add_search_args(\$q, \@qargs, \$s, $args{album}, 'album.name');
		$cap = "Search Album: $args{album}";
	}

	if(scalar @qargs > 0) {
		$s =~ s/^r_(.*)/\1 DESC/;
		$q .= " AND song.artist_id=artist.id AND song.album_id=album.id".
		      " GROUP BY artist_id, album_id ORDER BY sort";
		print_artistlist_table($dbh, \%session, $cap, $q, @qargs);
	} else {
		print "Error: No search terms specified.\n";
	}
	printftr;
}
elsif($cmd eq 'alllist') {
	printhtmlhdr;
	printhdr($conf{allstyle});
	my $q = ("SELECT artist.name as artist,album.name as album,song.*," .
		 "song.artist_id as arid, song.album_id as alid" .
		 " FROM song,artist,album" .
		 " WHERE present");
	my @qargs;
	my $cap;
	my $limit = $conf{alllist_limit};
	my $s = $args{sort};
	$s =~ s/\W//g;
	if($args{any} =~ /\S/) {
		add_search_args(\$q, \@qargs, \$s, $args{any},
			'artist.name', 'title', 'album.name');
		$cap = "Search any: $args{any}";
	}
	if($args{artist} =~ /\S/) {
		add_search_args(\$q, \@qargs, \$s, $args{artist}, 'artist.name');
		$cap = "Search Artist: $args{artist}";
	}
	if($args{album} =~ /\S/) {
		add_search_args(\$q, \@qargs, \$s, $args{album}, 'album.name');
		$cap = "Search Album: $args{album}";
	}
	if($args{title} =~ /\S/) {
		add_search_args(\$q, \@qargs, \$s, $args{title}, 'title');
		$cap = "Search Title: $args{title}";
	}
	if($args{filename} =~ /\S/) {
		add_search_args(\$q, \@qargs, \$s, $args{filename}, 'filename');
		$cap = "Search Filename: $args{filename}";
	}

	if($args{artist_id}) {
		$q .= " AND song.artist_id=?";
		push @qargs, $args{artist_id};
		$s = "artist.name" unless $s;
		$cap = sprintf($args{cap}, $args{artist_id});
	}
	if($args{album_id}) {
		$q .= " AND song.album_id=?";
		push @qargs, $args{album_id};
		$s = "album.name" unless $s;
		$cap = sprintf($args{cap}, $args{album_id});
	}
	if($args{encoding}) {
		$s = "artist.name" unless $s;
		add_search_args(\$q, \@qargs, \$s, $args{encoding}, 'encoding');
		$cap = "Search Encoding: $args{encoding}";
	}
	if($args{rand}) {
		$limit = 0 + $args{rand};
		$s = "rand()";
	}

	if($s) {
		$s =~ s/^r_(.*)/\1 DESC/;
		$q .= " AND song.artist_id=artist.id AND song.album_id=album.id ".
		      " AND filename LIKE '/%' ".
		      " ORDER BY $s,album.name,track,artist.name,title";
		print_alllist_table($dbh, \%args, \%session, $cap, $q, $limit, @qargs);
	} else {
		print "Error: No search terms specified.\n";
	}
#	printf "[[%s]]\n", $bla;
	printftr;
}
elsif($cmd eq 'seealso') {
	printhtmlhdr;
	printhdr($conf{allstyle});
	print <<EOF;
<center id=hdr>$args{cap}</center>
EOF
	my $baseurl = "$self?";
	foreach(keys %args) {
		next if $_ eq "cmd";
		$baseurl .= "$_=" . encurl($args{$_}) . "&";
	}
	print_albums_row($dbh, $baseurl, \%args, $args{cap}, $args{artist_id});
	printftr;
}
elsif($cmd eq 'sql') {
	require_write_access;

	printhtmlhdr;
	printhdr($conf{allstyle});

	printf <<EOF, enchtml($args{sql}), $args{countonly}? "checked":"";
SQL-query:<br>
<form action="$self" method=get>
  <input type=hidden name=cap value="SQL-query">
  <input type=hidden name=cmd value=sql>
<code>
SELECT ... FROM ... WHERE ... AND <input type=text size=80 name=sql value="%s">
<input type=checkbox name=countonly %s> count only
</code>
</form>
EOF

	if($args{sql}) {
		if($args{countonly}) {
			my ($count) = $dbh->selectrow_array("SELECT COUNT(*)".
				" FROM song,artist,album WHERE present " .
				" AND song.artist_id=artist.id AND song.album_id=album.id AND " .
				$args{sql});
			print "Count: $count\n";
		} else {
			print_alllist_table($dbh, \%args, \%session, "User SQL-query",
				"SELECT artist.name as artist,album.name as album,song.*," .
				"song.artist_id as arid, song.album_id as alid" .
				" FROM song,artist,album WHERE present " .
				" AND song.artist_id=artist.id AND song.album_id=album.id AND " .
				$args{sql});
		}
	}
	printftr;
}
elsif($cmd eq 'recent') {
	printhtmlhdr;
	printhdr($conf{allstyle});
	my $maxage = $args{days} * 86400;
	my $s = $args{sort} || "r_time_added";
	$s =~ s/\W//g;
	$s =~ s/^r_(.*)/\1 DESC/;
	print_alllist_table($dbh, \%args, \%session,
		"Most recent $n songs" . ($args{np}? " (never played yet)":""),
		"SELECT artist.name as artist,album.name as album,song.*," .
		"song.artist_id as arid, song.album_id as alid" .
		" FROM song,artist,album WHERE present AND filename LIKE '/%'" .
		" AND song.artist_id=artist.id AND song.album_id=album.id" .
		" AND unix_timestamp(now()) - unix_timestamp(time_added) < $maxage" .
		($args{np}? " AND unix_timestamp(last_played) = 0":"") .
		" ORDER BY $s,album.name,track,artist.name,title", 500);
	printftr;
}
elsif($cmd eq 'maint') {
	printhtmlhdr;
	printhdr($conf{allstyle});
	print <<EOF;
<script language="Javascript">
<!--
function verifyfull() {
   return confirm("Are you sure you want to perform a full update? You might lose changes you made in the database!");
}
// -->
</script>
<center id=hdr>Update Database</center>
<form action="$self" method=get>
 <input type=hidden name=cmd value=update>
 <input type=submit value="Quick Update"> (leave existing files alone).<br><br>
 <input type=submit value="Full Update" name=action_full onClick="return verifyfull();"> (re-enter info for existing files (<b>dangerous</b>)).<br><br>
 Updating the database will take a while; don't press the 'stop' button on your browser if you want this to succeed.
</form>
EOF
	printftr;
}
elsif($cmd eq 'update') {
	require_write_access;
	print $query->header(-type=>'text/plain');
	my $arg = "";
	$arg = "-f" if $args{action_full};
	print `$conf{progdir}/soepkiptng_update $arg 2>&1`;
}
elsif($cmd eq 'edit') {
	printhtmlhdr;
	printhdr($conf{editstyle});
	print_edit_page($dbh, \%args);
	printftr;
}
elsif($cmd eq 'shoutcast') {
	printhtmlhdr;
	printhdr($conf{allstyle});
	print_shoutcast_page($dbh, \%args);
	printftr;
}
elsif($cmd eq 'download') {
	$args{id} =~ /(\d+)/;
	my $id = $1;
	my ($file) = $dbh->selectrow_array("SELECT filename FROM song WHERE id=$id")
		or die "id $id not found in database\n";

	open F, $file or die "$file: $!\n";
	print $query->header(-type=>'application/octet-stream', -Content_length=>(-s F));
	while(read F, $_, 4096) { print; }
	close F;
}
elsif($cmd eq 'lists') {
        printhtmlhdr;
	printhdr($conf{allstyle});
	print_lists($dbh);
	printftr;
}
else {
	printhtmlhdr;
	print "oei: $cmd\n";
}

untie %session;
$dbh->disconnect();

