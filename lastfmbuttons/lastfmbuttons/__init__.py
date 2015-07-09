# Copyright (C) 2011 Bruno Finger <bruno.finger12@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#


from xl import event
from xlgui import guiutil
from xlgui import main
from xl import settings
import os
import os.path
import urllib
import urllib2
import gtk
import xlgui
import lfm_prefs

PLUGIN = None

def enable(exaile):
    if (exaile.loading):
        event.add_callback(_enable, 'exaile_loaded')
    else:
        _enable(None, exaile, None)
 
def disable(exaile):
	global PLUGIN
	PLUGIN.removeButton()
 
def _enable(eventname, exaile, nothing):
	global PLUGIN
	PLUGIN = LastFmButton(exaile)

def get_preferences_pane():
	return lfm_prefs

####################################################

class LastFmButton:
	def __init__(self, exaile):
		self.api_key = '306014e9c8688aa80edd9a86e86ecace'
		self.exaile = exaile
		self.volume_control = xlgui.main.mainwindow().volume_control
		self.addButton()
		self.session = Session()
		self._sessionpath = self.session.getPath()
		self._statuspath = os.getenv('HOME') + '/.local/share/exaile/lastfmbuttons.status'
		self.status = '0'
		
		if os.path.isfile(self._statuspath):
			file = open(self._statuspath, 'r')
			self.status = file.readline()[0]
		else:
			file = open(self._statuspath, 'w')
			file.write('0')
			file.close()
		
		if self.status != '2':
			print 'Will attempt to create a new Session.'
			self.authenticate()
			file = open(self._statuspath, 'w')
			file.write(self.status)
			file.close()
		else:
			if os.path.isfile(self._sessionpath):
				self.session.readSession()
		print 'Last.fm Buttons loaded.'
			
	
	def removeButton(self):
		volume_control = guiutil.VolumeControl()
		guiutil.gtk_widget_replace(self.volume_control, volume_control)
		self.volume_control = volume_control
		print 'Last.fm Buttons disabled. You\'ll need to restart Exaile to successfully enable them again.'
		
	def addButton(self):
		self.createButton()
		volume_control = guiutil.VolumeControl()
		volume_control.child.add(self.lovebutton)
		volume_control.child.add(self.banbutton)
		self.lovebutton.show()
		self.banbutton.show()
		guiutil.gtk_widget_replace(self.volume_control, volume_control)
		self.volume_control = volume_control
		print 'Last.fm Buttons enabled.'
	
	def createButton(self):
		self.lovebutton = gtk.Button()
		self.lovebutton.connect('clicked', self.loveButtonActionPerformed)
		loveimage = gtk.Image()
		loveimage.set_from_file(os.getenv('HOME') + '/.local/share/exaile/plugins/lastfmbuttons/images/love.png')
		self.lovebutton.set_image(loveimage)
		
		self.banbutton = gtk.Button()
		self.banbutton.connect('clicked', self.banButtonActionPerformed)
		banimage = gtk.Image()
		banimage.set_from_file(os.getenv('HOME') + '/.local/share/exaile/plugins/lastfmbuttons/images/ban.png')
		self.banbutton.set_image(banimage)
	
	def loveButtonActionPerformed(self, object):
		track = self.exaile.player.current
		tracktitle = track.get_tag_display('title')
		trackartist = track.get_tag_display('artist')
		self.love(tracktitle, trackartist)
	
	def banButtonActionPerformed(self, object):
		track = self.exaile.player.current
		tracktitle = track.get_tag_raw('title')
		trackartist = track.get_tag_raw('artist')
		self.ban(tracktitle, trackartist)
	
	def authenticate(self):
		if self.status == '0':
			token = self.getToken() # Step 2
			print 'Token retrieved: ' + token
			self.askPermission(token) # Step 3
			self.status = '1'
			print 'Exaile needs to be restarted to continue with authentication.'
			file = open(os.getenv('HOME') + '/.local/share/exaile/lastfmbuttons.token', 'w')
			file.write(token)
			file.close()
		elif self.status == '1':
			file = open(os.getenv('HOME') + '/.local/share/exaile/lastfmbuttons.token', 'r')
			token = file.readline()
			print 'Token: \'' + token + '\''
			file.close()
			self.getSession(token) # Step 4
			self.status = '2'
			file = open(self._statuspath, 'w')
			file.write(self.status)
			file.close()
			print 'Authentication done.'
		elif self.status == '3':
			print 'No Authentication needed.'
		else:
			print 'Invalid status. What happened?'
	
	
	"""
	auth.getToken
	
	Authentication Step 2/4
	(Get an API Key is Step 1 of the Authentication proccess.)
	
	From Last.fm:
	
	Authentication tokens are API account specific. They are valid for 60 minutes from the moment they are granted.
	"""
	def getToken(self):
		tokenHtml = urllib2.urlopen('http://ws.audioscrobbler.com/2.0/?method=auth.getToken&api_key=' + self.api_key)
		tokenAux = tokenHtml.read()
		tokenHtml.close()
		token = tokenAux.split()[5].split('<token>')[1].split('</token></lfm>')[0]
		return token
		
	"""
	Authentication Step 3/4
	
	Needs to open a web browser requesting user permission to use the plugin.
	"""
	def askPermission(self, token):
		url = '"http://www.lastfm.com/api/auth?api_key=' + self.api_key + '&token=' + token + '"'
		os.system('/usr/bin/xdg-open ' + url)
	
	"""
	auth.getSession
	
	Authentication Step 4/4
	
	From Last.fm:
	
	Session keys have an infinite lifetime by default. You are recommended to store the key securely.
	Users are able to revoke privileges for your application on their Last.fm settings screen,
	rendering session keys invalid.
	-----
	Returns True if everything went OK, False if there was a problem.
	"""
	def getSession(self, token):
		session = None
		print 'Trying to generate api_sig for token ' + token
		api_sigHtml = urllib2.urlopen('http://lastfmbuttons.appspot.com/generate_sig?token=' + token + '&method=auth.getSession')
		api_sig = api_sigHtml.read()
		print 'api_sig generated: ' + api_sig
		
		print 'Trying to generate Session'
		sessionHtml = urllib.urlopen('http://ws.audioscrobbler.com/2.0/?method=auth.getSession&token=' + token + '&api_key=' + self.api_key + '&api_sig=' + api_sig)
		sessionAux = sessionHtml.read().split('\n')
		print sessionAux
		
		if sessionAux[1] == '<lfm status=\"ok\">':
			print 'Status OK. Authenticated!'
			name = sessionAux[3].split('<name>')[1].split('</name>')[0]
			key = sessionAux[4].split('<key>')[1].split('</key>')[0]
			subscriber = False
			if sessionAux[5].split('<subscriber>')[1].split('</subscriber>')[0] == '1':
				subscriber = True
			session = Session(name, key, subscriber)
			print 'Session generation successful! sk = \'' + session.getKey() + '\''
			self.session = session
			self.session.saveSession()
		else:
			print 'There was an error retrieving a session key:\n'
			for line in sessionAux:
				print line
	
	"""
	track.love
	
	From Last.fm:
	Params

	track (Required) : A track name (utf8 encoded)
	artist (Required) : An artist name (utf8 encoded)
	api_key (Required) : A Last.fm API key.
	api_sig (Required) : A Last.fm method signature. See authentication for more information. <-
	sk (Required) : A session key generated by authenticating a user via the authentication protocol. <-
	---------
	Last.fm requires that all write methods use POST instead of GET, just to make things a little more complicated :)
	"""
	def love(self, track, artist):
		params = {}
		sk = self.session.getKey()
		print 'Session key: \'' + sk + '\''
		print 'Artist: \'' + artist + '\''
		print 'Track: \'' + track + '\''
		sigUrl = 'http://lastfmbuttons.appspot.com/generate_sig?method=track.love&artist=' + artist + '&sk=' + sk + '&track=' + track
		api_sigHtml = urllib.urlopen(sigUrl)
		api_sig = api_sigHtml.read()
		print 'api_sig: \'' + api_sig + '\''
		
		params['api_key'] = self.api_key
		params['api_sig'] = api_sig
		params['artist'] = artist
		params['method'] = 'track.love'
		params['sk'] = sk
		params['track'] = track
		
		paraux = urllib.urlencode(params)
		response = urllib.urlopen('http://ws.audioscrobbler.com/2.0/', paraux)
		print 'Loved ' + artist + ' - ' + track
		print response.read()
	
	
	"""
	Same as track.love
	"""
	def ban(self, track, artist):
		params = {}
		sk = self.session.getKey()
		print 'Session key: \'' + sk + '\''
		print 'Artist: \'' + artist + '\''
		print 'Track: \'' + track + '\''
		sigUrl = 'http://lastfmbuttons.appspot.com/generate_sig?method=track.ban&artist=' + artist + '&sk=' + sk + '&track=' + track
		api_sigHtml = urllib.urlopen(sigUrl)
		api_sig = api_sigHtml.read()
		print 'api_sig: \'' + api_sig + '\''
		
		params['api_key'] = self.api_key
		params['api_sig'] = api_sig
		params['artist'] = artist
		params['method'] = 'track.ban'
		params['sk'] = sk
		params['track'] = track
		
		paraux = urllib.urlencode(params)
		response = urllib.urlopen('http://ws.audioscrobbler.com/2.0/', paraux)
		print 'Loved ' + artist + ' - ' + track
		print response.read()


#####################################################



class Session():
	def __init__(self, name=None, key=None, subscriber=None):
		self._name = name
		self._key = key
		self._subscriber = subscriber
		self._path = os.getenv('HOME') + '/.local/share/exaile/lastfmbuttons.session'
		
	def getName(self):
		return self._name
	
	def setName(self, name):
		self._name = name
	
	def getKey(self):
		return self._key
	
	def setKey(self, key):
		self._key = key
	
	def isSubscriber(self):
		return self._subscriber
	
	def setSubscriber(self, subscriber):
		self._subscriber = subscriber
	
	def getPath(self):
		return self._path
		
	def setPath(self, path):
		self._path = path
	
	def saveSession(self):
		print 'Saving Session to file...'
		print str(self)
		string = self.getName() + ' ' + self.getKey() + ' '
		if self.isSubscriber():
			string = string + '1'
		else:
			string = string + '0'
		file = open(self._path, 'w')
		file.write(string)
		file.flush()
		file.close()
		print 'File closed.'
	
	def readSession(self):
		print 'Reading Session from file...'
		file = open(self._path, 'r')
		lines = file.readline().split(' ')
		file.close()
		print lines
		name = lines[0]
		key = lines[1]
		subscriber = lines[2][0]
		self.setName(name)
		self.setKey(key)
		if subscriber == '1':
			self.setSubscriber(True)
		else:
			self.setSubscriber(False)
		print str(self)
	
	def __str__(self):
		return 'Login: ' + self.getName() + '\nSession Key: ' + self.getKey() + '\nSubscriber: ' + str(self.isSubscriber())
		
		
	
