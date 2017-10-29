#!/usr/bin/python
# coding=UTF-8

# For the AliExpress TJCTM24024-SPI 2.4" 240x320 SPI TFT screen I used, I used this to get the display working:
# (From http://www.sudomod.com/forum/viewtopic.php?t=2312)
# sudo raspi-config
# Overscan: disabled, SPI: Enabled. Reboot.
# sudo modprobe fbtft_device custom name=fb_ili9341  gpios=reset:25,dc:24,led:18 speed=16000000 bgr=1
# sudo nano /etc/modules
# Add to the bottom...
#   spi-bcm2835
#   fbtft_device
# sudo nano /etc/modprobe.d/fbtft.conf (probably empty)
#   options fbtft_device name=fb_ili9341 gpios=reset:25,dc:24,led:18 speed=16000000 bgr=1 rotate=270 custom=1
# reboot
# sudo apt-get install cmake
# git clone https://github.com/tasanakorn/rpi-fbcp
# cd rpi-fbcp/
# mkdir build
# cd build/
# cmake ..
# make
# sudo install fbcp /usr/local/bin/fbcp
# fbcp (Screen will show the default RPi X session
# sudo nano /etc/rc.local (Now going to make this happen on boot)
# Add before the 'exit' line: fbcp&
# Save and reboot. 

##  Do a sudo pip install for feedparser, pyown

########
##  Import lots of libraries.
########
import time
import datetime
import feedparser
import sys
import pygame
import os
import io
import pyowm
from urllib2 import urlopen
from gpiozero import Button

# Which GPIO pins are the PTMs wired from GND to? Use GPIO number (not pin)
b1 = Button(17)
b2 = Button(27)
b3 = Button(22)

# OpenWeatherMap API key...
weatherKey='INSERT HERE'
owm = pyowm.OWM(weatherKey)

#########
##  Set up globals
########
pygame.init()
lcd = pygame.display.set_mode((720, 480), pygame.FULLSCREEN)
pygame.mouse.set_visible(False)
# Dampen down the colours a bit to help limit screen burn-in.
white = (240, 240, 240)
black = (0, 0, 0)
red = (200, 0, 0)
yellow = (200, 200, 0)
green = (0, 200, 0)
grey = (175, 175, 175)

########
##  General-purpose functions.
########

def left(s, amount):
  return s[:amount]

def right(s, amount):
  return s[-amount:]

def drawText(msgText, fontSize, xLoc, yLoc, colour=black):
  fontName = pygame.font.match_font('arial')
  font = pygame.font.Font(fontName, fontSize)
  text_surface = font.render(msgText, True, colour)
  lcd.blit(text_surface, (xLoc, yLoc))

########
##  Functions for the news/weather page
########

def renderNews():
  # Display top 3 headlines from BBC RSS feed.
  d = feedparser.parse('http://feeds.bbci.co.uk/news/rss.xml?edition=uk')

  # Show BBC logo.
  image = pygame.image.load('/home/pi/SB-Pi-TFT/bbc.png')
  image = pygame.transform.scale(image, [204,106]) # Original is 1024 x 576
  lcd.blit(image, (250, 10))

  yPos = 150 # y location of the first headline. 25

  for nextHeadline in range (3):
    headline= d['entries'][nextHeadline]['title'] + "."
    
    try:
      if len(headline) > 26:
        # Track down a space before starting a new line.
        spaceLoc = 26
        gotOne = False

        while gotOne == False and spaceLoc < len(headline):
          if headline[spaceLoc] == ' ':
            gotOne = True

          spaceLoc += 1

        drawText(headline[0:spaceLoc], 40, 10, yPos, white)
        drawText(headline[spaceLoc:], 40, 10, yPos + 40, white)
      else:
        drawText(headline, 40, 10, yPos + 20, white)

      yPos += 100
      
      pygame.display.update()
    except:
      print "News error:", sys.exc_info()[0]
      print "News error:", sys.exc_info()[1]
      with open("test.txt", "a") as myfile:
        myfile.write("News error:", sys.exc_info()[0]) 
        myfile.write("News error:", sys.exc_info()[1])
      
def renderWeatherNow():
  try:
    observation = owm.weather_at_place('Market Deeping,uk')
    w = observation.get_weather()

    weather = w.get_detailed_status()
    weather = weather[0].upper() + weather[1:]
    currTemp = w.get_temperature(unit='celsius')
    humid = w.get_humidity()
    wind = w.get_wind() 
    windspeed = int(wind['speed'])
    sunrise = w.get_sunrise_time('iso')
    sunrise = right(sunrise,11)
    sunrise = left(sunrise,8)
    sunset = w.get_sunset_time('iso')
    sunset = right(sunset,11)
    sunset = left(sunset,8)
    cloud = w.get_clouds()

    # Draw the weather state at the top.
    drawText(weather, 60, 20, 15, white)
    
    # Show the weather icon
    icon = w.get_weather_icon_name()
    renderWeatherIcon(icon, 20, 80, 250, 250)

    # Show the headline figures to the right.
    drawText("Temperature: " + str(int(currTemp['temp'])) + "C", 45, 320, 100, white)
    drawText("Wind: " + str(windspeed) + "m/s", 45, 320, 150, white)
    drawText("Cloud: " + str(cloud) + "%", 45, 320, 200, white)
    drawText("Sunrise: " + sunrise[:5], 45, 320, 250, white)
    drawText("Sunset: " + sunset[:5], 45, 320, 300, white)

    # Time and date at the bottom
    theTime = str(datetime.datetime.now().time())
    theDate = time.strftime("%d/%m/%Y")
    drawText(theTime[0:5] + ", " + theDate,60,20,390, white)

    # Paint the screen
    pygame.display.update()
  except:
    print("Problems!")
    print "Weather error:", sys.exc_info()[0]
    print "Weather error:", sys.exc_info()[1]
      
def renderWeather():
  # Renders longer-term  weather onto the display
  observation = owm.weather_at_place('Market Deeping,uk')
  w = observation.get_weather()

  weather = w.get_detailed_status()
  weather = weather[0].upper() + weather[1:]

  try:
    # Do the 3-hourly forecast...
    hourlyFc = owm.three_hours_forecast('Market Deeping,uk')
    f = hourlyFc.get_forecast()
    lst = f.get_weathers()

    pygame.draw.rect(lcd, grey, (0, 95, 320, 73))
    x=15
    for weather in lst:
      if x < 300:
        icon = weather.get_weather_icon_name()
        theTemp = int(weather.get_temperature(unit='celsius')['temp'])
        forecastTime = weather.get_reference_time('iso')
        forecasthour = int(forecastTime[11:13])
        if forecasthour<12:
          suffix = "am"
        elif forecasthour == 0:
          forecasthour = 12
          suffix = "am"
        else:
          forecasthour -= 12
          suffix = "pm"
        renderWeatherIcon(icon, x, 100, 40, 40)
        drawText(str(forecasthour) + suffix, 15, x+3, 95, white)
        drawText(str(theTemp) + "C", 15, x + 22 - len(str(theTemp) + "C") * 5, 145, white)
        drawText(weather.get_status(), 10, x + 20 - len(weather.get_status()) * 3, 133, white)
        
        x += 50
        
    # Do the 6-day forecast...
    dailyFc = owm.daily_forecast('Market Deeping,uk', limit=6)
    f = dailyFc.get_forecast()
    lst = f.get_weathers()
    pygame.draw.rect(lcd, grey, (0, 170, 320, 85))
    x=15
    for weather in lst:
      if x < 300:
        icon = weather.get_weather_icon_name()
        theTemp = int(weather.get_temperature(unit='celsius')[u'day'])
        forecastTime = weather.get_reference_time('iso')
        forecastday = str(forecastTime[8:10])

        if forecastday.endswith('1'):
          suffix = "st"
        elif forecastday.endswith('2'):
          suffix = "nd"
        elif forecastday.endswith('3'):
          suffix = "rd"
        else:
          suffix = "th"

        renderWeatherIcon(icon, x, 177, 40, 40)
        drawText(str(forecastday) + suffix, 15, x+3, 170, white)
        drawText(str(theTemp) + "C", 15, x + 22 - len(str(theTemp) + "C") * 5, 220, white)
        drawText(weather.get_status(), 10, x + 20 - len(weather.get_status()) * 3, 210, white)
        
        x += 50
        
    pygame.display.update()
  except:
    # Weather trouble...
    print "Weather error:", sys.exc_info()[0]
    print "Weather error:", sys.exc_info()[1]
    drawText("Weather unavailable",20, 5, 5)
    pygame.display.update()

    
def renderWeatherIcon(icon, xPos, yPos, xSize=90, ySize=90):
  # Renders a weather icon onto the display
  image_url = "http://openweathermap.org/img/w/" + icon + ".png"
  image_str = urlopen(image_url).read()
  image_file = io.BytesIO(image_str)
  image = pygame.image.load(image_file)
  image = pygame.transform.scale(image, [xSize,ySize])
  lcd.blit(image, (xPos, yPos))

def paintTime(numSecs = 5):
  # Show the time / date at the bottom for 5s, then update everything else.
  for x in range(numSecs * 2):
    theTime = str(datetime.datetime.now().time())
    theDate = time.strftime("%d/%m/%Y")
    pygame.draw.rect(lcd, white, (0, 185, 320, 225))
    drawText(theTime[0:8] + ", " + theDate,32,5,205)
    pygame.display.update()
    time.sleep(0.5)

def showTime():
  theTime = str(datetime.datetime.now().time())
  theDate = time.strftime("%d/%m/%Y")
  drawText(theTime[0:8],175,25,100, white)
  drawText(theDate, 75, 40, 280, white)
  pygame.display.update()
  

########
## Multi-day forecast code starts
########

def multiDay():
  # Grab forecast
  fc = owm.daily_forecast('London,uk', limit=6)
  # Render it

########
## Main program loop
########

def main():
  whichHeadline = 0
  lcd.fill(white)
  
  while True:
    # Show weather for now
    try:
      lcd.fill(black)
      renderWeatherNow()
      time.sleep(6)
    except:
      time.sleep(0.25)
    
    # Show time / date
    lcd.fill(black)
    for n in range(30):
      showTime()
      time.sleep(0.2)
      lcd.fill(black)

      if b3.is_pressed:
        break

    # Show the news...
    try:
      lcd.fill(black)
      renderNews()
      time.sleep(6)
    except:
      print "Unexpected error:", sys.exc_info()[0]          
      print "Unexpected error:", sys.exc_info()[1]
      time.sleep(0.25)

    # Show time / date again
    lcd.fill(black)
    for n in range(30):
      showTime()
      time.sleep(0.2)
      lcd.fill(black)

      if b3.is_pressed:
        break
      
main()

'''
if __name__ == '__main__':
  try:
    main()
  except KeyboardInterrupt:
    pass
  finally:
    pygame.quit()   # stops the PyGame engine
    sys.exit()
'''
