package MP3::Tag;

################
#
# provides a general interface for different modules, which can read tags
#
# at the moment MP3::Tag works with MP3::Tag::ID3v1 and MP3::Tag::ID3v2

use strict;
use MP3::Tag::ID3v1;
use MP3::Tag::ID3v2;
use MP3::Tag::File;
use vars qw/$VERSION %config/;

$VERSION="0.30";

=pod

=head1 NAME

Tag - Module for reading tags of MP3 audio files

=head1 SYNOPSIS

  use Tag;
  $mp3 = MP3::Tag->new($filename);
  $mp3->getTags;

  if (exists $mp3->{ID3v1}) {
    $id3v1 = $mp3->{ID3v1};
    print $id3v1->song;
    ...
  }

  if (exists $mp3->{ID3v2}) {
    ($name, $info) = $mp3->{ID3v2}->getFrame("TIT2");
    ...
  }

  $mp3->close();

=head1 AUTHOR

Thomas Geffert, thg@users.sourceforge.net

=head1 DESCRIPTION

Tag is a wrapper module to read different tags of mp3 files. 
It provides an easy way to access the functions of seperate moduls
which do the handling of reading/writing the tags itself.

At the moment MP3::Tag::ID3v1 and MP3::Tag::ID3v2 are supported.

!! As this is only a beta version, it is very likely that the design 
!! of this wrapper module will change soon !!

=over 4

=item new()

 $mp3 = MP3::Tag->new($filename);

Creates a mp3-object, which can be used to retrieve/set
different tags.

=cut

sub new {
  my $class = shift;
  my $filename = shift;
  my $mp3data;
  if (-f $filename) {
    $mp3data = MP3::Tag::File->new($filename);
  }
  # later it should hopefully possible to support also http/ftp sources
  # with a MP3::Tag::Net module or something like that
  if ($mp3data) {
    my $self={filename=>$mp3data};
    bless $self, $class;
    return $self;
  }
  return undef;
}

=pod

=item getTags()

  @tags = $mp3->getTags;

Checks which tags can be found in the mp3-object. It returns
a list @tags which contains strings identifying the found tags.

Each found tag can be accessed then with $mp3->{tagname} .

Use the information found in MP3::Tag::ID3v1 and MP3::Tag::ID3v2
to see what you can do with the tags.

=cut 

################ tag subs

sub getTags {
  my $self = shift;
  my (@IDs, $ref);
  if (exists $self->{gottags}) {
    push @IDs, "ID3v1" if exists $self->{ID3v1};
    push @IDs, "ID3v2" if exists $self->{ID3v2};
  } elsif ($self->{filename}->open()) {
    $self->{gottags}=1;
    if (defined ($ref = MP3::Tag::ID3v2->new($self->{filename}))) {
      $self->{ID3v2} = $ref;
      push @IDs, "ID3v2";
    }
    if(defined ($ref = MP3::Tag::ID3v1->new($self->{filename}))) {
      $self->{ID3v1} = $ref;
      push @IDs, "ID3v1";
    }
  }
  return @IDs;
}

=pod

=item newTag()

  $tag = $mp3->newTag($tagname);

Creates a new tag of the given type $tagname. You
can access it then with $mp3->{$tagname}. At the
moment ID3v1 and ID3v2 are supported as tagname.

Returns an tag-object: $mp3->{$tagname}.

=cut

sub newTag {
  my $self = shift;
  my $whichTag = shift;
  if ($whichTag =~ /1/) {
    $self->{ID3v1}= MP3::Tag::ID3v1->new($self->{filename},1);
    return $self->{ID3v1};
  } elsif ($whichTag =~ /2/) {
    $self->{ID3v2}= MP3::Tag::ID3v2->new($self->{filename},1);
    return $self->{ID3v2};
  }
}

#only as a shortcut to {filename}->close to explicitly close a file
=pod

=item close()

  $mp3->close;

You can use close() to explicitly close a file. Normally this is done
automatically by the module, so that you don't need to do this.

=cut

sub close {
  my $self=shift;
  $self->{filename}->close;
}

=pod

=item genres()

  $allgenres = $mp3->genres;
  $genreName = $mp3->genres($genreID);
  $genreID   = $mp3->genres($genreName);

Returns a list of all genres (reference to an array), or the according 
name or id to a given id or name.

This function is only a shortcut to MP3::Tag::ID3v1->genres.

This can be also called as MP3::Tag->genres;
=cut

sub genres {
  # returns all genres, or if a parameter is given, the according genre
  my $self=shift;
  return MP3::Tag::ID3v1::genres(shift);
}

=pod

=item autoinfo()

  ($song, $track, $artist, $album) = $mp3->autoinfo();
  $info_hashref = $mp3->autoinfo();

autoinfo() returns information about the song name, song number,
artist number and album name. It can get this information from an
ID3v1-tag, an ID3v2-tag and from the filename itself.

It will as default first try to find a ID3v2-tag to get this
information. If this cannot be found it tries to find a ID3v1-tag and
if this is not present either, it will use the filename to retrieve
the information.

You can change the order of this with the config() command.

autoinfo() returns an array with the information or a hashref. The hash
then has the keys song, track, artist, album where the information is
stored.

=cut

sub autoinfo() {
  my ($self) = shift;

  my @order;
  if (exists $config{autoinfo}) {
    @order = @{$config{autoinfo}};
  } else {
    @order = ("ID3v2","ID3v1","filename");
  }

  $self->getTags unless exists $self->{gottags};

  my ($song, $track, $artist, $album)=("","","","");
  foreach my $part (@order) {
    if (exists $self->{$part}) {
      #get the info
      $song=$self->{$part}->song;
      $track=$self->{$part}->track;
      $artist=$self->{$part}->artist;
      $album=$self->{$part}->album;
      last;
    }
  }
  return ($song, $track, $artist, $album);
}

=pod

=item config

  MP3::Tag->config("item", options, ...);

Possible items are:

* autoinfo

  Configure the order in which ID3v1-, ID3v2-tag and filename are used
  by autoinfo.  options can be "ID3v1","ID3v2","filename". The order
  in which they are given to config also sets the order how they are
  used by autoinfo. If an option is not present, it will not be used
  by auotinfo.

  $mp3->config("autoinfo","ID3v1","ID3v2","filename");

    sets the order to check first ID3v1, then ID3v2 and last the
    Filename

  $mp3->config("autoinfo","ID3v1","filename","ID3v2");

    sets the order to check first ID3v1, then the Filename and last
    ID3v2. As the filename will be always present ID3v2 will be
    checked never.

  $mp3->config("autoinfo","ID3v1","ID3v2");

    sets the order to check first ID3v1, then ID3v2. The filename will
    be never used.

* Later this will be used probably to configure more things.

=cut

sub config() {
  my ($self, $item, @options) = @_;

  $config{lc $item}=\@options;
}


sub DESTROY {
  my $self=shift;
  if (exists $self->{filename}) {
    $self->{filename}->close;
  }
}

1;

=pod

=head1 SEE ALSO

L<MP3::Tag::ID3v1>, L<MP3::Tag::ID3v2>, L<MP3::Tag::File>

=cut
