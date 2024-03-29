#!/usr/bin/python
# coding=UTF-8

# sudo pip install feedparser, pyowm, rpi_backlight --break-system-packages
# To prevent the password warning on boot, do rm /etc/xdg/lxsession/LXDE-pi/sshpwd.sh
# To make clock start on reboot, add 'python /home/pi/SB-Pi-TFT/tft.py' to the bottom of /home/pi/.bashrc
# NOTE: This isn't perfect, as whenever you SSH in it'll launch another instance of tft.py.

########
##  Import lots of libraries.
########
from rpi_backlight import Backlight
import pytz   # Used for weather, to ensure that sunrise/sunset times are GMT.
import time
import datetime
import feedparser
import sys
import pygame
import os
import io
import pyowm
import math                      # Trig functions used for the analogue clock rendering.
from urllib.request import urlopen
import RPi.GPIO as GPIO # For the PTM interrupts.
import csv
import random

# OpenWeatherMap API key...
weatherKey='YOUR KEY HERE'
owm = pyowm.OWM(weatherKey)
mgr = owm.weather_manager()

# Use this initially. Will get corrected after the main loop has run once.
sunrise = datetime.datetime.now()
sunset = datetime.datetime.now()
      
# Which GPIO pins are the PTMs wired from GND to? Use GPIO number (not pin). Pin 22 has the right switch. 17 and 27 are the others.
GPIO.setmode(GPIO.BCM)
GPIO.setup(22, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(17, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(27, GPIO.IN, pull_up_down=GPIO.PUD_UP)

def mid_callback(channel):
    # Tried using GPIO.remove_event_detect(27) while this runs, but it causes a seg fault.
    global callbackLock

    if callbackLock == False:
        callbackLock == True
        global whatsOn
        global clockStyle
        global weatherStyle
        # Use middle for toggling views. 
        if whatsOn == 'clock':
            if clockStyle == 'analogue':
                clockStyle = 'digital'
                pygame.draw.rect(lcd, grey, (0, 0, 360, 70))
                drawText("Changed to 'Digital'", 40, 10, 10, black)
                pygame.display.update()
            elif clockStyle == 'digital':
                clockStyle = 'analogue'
                pygame.draw.rect(lcd, grey, (0, 0, 360, 70))
                drawText("Changed to 'Analogue'", 40, 10, 10, black)
                pygame.display.update()
                
        elif whatsOn == 'weather':
            if weatherStyle == 'normal':
                weatherStyle = 'detail'
                pygame.draw.rect(lcd, grey, (0, 0, 360, 70))
                drawText("Changed to 'detail'", 40, 10, 10, black)
                pygame.display.update()
            elif weatherStyle == 'detail':
                weatherStyle = 'brief'
                pygame.draw.rect(lcd, grey, (0, 0, 360, 70))
                drawText("Changed to 'brief'", 40, 10, 10, black)
                pygame.display.update()
            else:
                weatherStyle = 'normal'
                pygame.draw.rect(lcd, grey, (0, 0, 360, 70))
                drawText("Changed to 'normal'", 40, 10, 10, black)
                pygame.display.update()    
        else:
            print("middle button pushed")
        
        # Resume callbback processing.
        time.sleep(1)
        callbackLock = False

def left_callback(channel):  
    print ("Left")
    pygame.quit()   # stops the PyGame engine, quits the app.
    sys.exit()

def right_callback(channel):  
    print ("Right")

GPIO.add_event_detect(17, GPIO.FALLING, callback=left_callback) 
GPIO.add_event_detect(27, GPIO.FALLING, callback=mid_callback) 
GPIO.add_event_detect(22, GPIO.FALLING, callback=right_callback) 
    
#########
##  Set up globals
########
pygame.init()
#lcd = pygame.display.set_mode((720, 480), pygame.FULLSCREEN)
lcd = pygame.display.set_mode((800, 480), pygame.FULLSCREEN)
#lcd = pygame.display.set_mode((800, 480))
pygame.display.set_caption('Bedside Clock v1.0')
pygame.mouse.set_visible(False)
callbackLock = False # Prevent multiple callbacks when users hit the button.
# Dampen down the colours a bit to help limit screen burn-in.
white = (240, 240, 240)
black = (0, 0, 0)
red = (230, 0, 0)
yellow = (200, 200, 0)
green = (0, 200, 0)
grey = (175, 175, 175)

whatsOn = ''
clockStyle = 'analogue'
weatherStyle = 'brief'

def loadQuotes():
    loc = os.getcwd() # FIX THIS. Should pick up the location of this PY file.
    loc = '/home/pi/SB-Pi-Bedside_Clock'

    # Open the times list...
    #with open(loc + '/quotes.csv', 'rb') as csvfile:
    with open(loc + '/quotes.csv') as csvfile:
        content = csv.reader(csvfile, delimiter='|', quotechar='"')
        output = list(content)

    return output

# Load up literature  (once)...
quotes = loadQuotes()

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
  image = pygame.image.load('/home/pi/SB-Pi-Bedside_Clock/bbc.png')
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
      print ("News error:", sys.exc_info()[0])
      print ("News error:", sys.exc_info()[1])
      with open("test.txt", "a") as myfile:
        myfile.write("News error:", sys.exc_info()[0]) 
        myfile.write("News error:", sys.exc_info()[1])

def is_dst(zonename):
  tz = pytz.timezone(zonename)
  now = pytz.utc.localize(datetime.datetime.utcnow())
  return now.astimezone(tz).dst() != datetime.timedelta(0)

def renderWeatherNow():
  global sunrise  # 26/6/23 NEW
  global sunset   #
  observation = mgr.weather_at_place('Market Deeping,uk')
  w = observation.weather
  currTemp = w.temperature(unit='celsius')
  icon = w.weather_icon_name

  sunrise = w.sunrise_time(timeformat='date')
  sunset = w.sunset_time(timeformat='date')

  # Are we in British Summer Time? If so, add an hour to UTC
  if (is_dst('Europe/London')):
      sunrise = sunrise + datetime.timedelta(hours=1)
      sunset = sunset + datetime.timedelta(hours=1)
      
  srise = '{:%H:%M}'.format(sunrise)
  sset = '{:%H:%M}'.format(sunset)

  weather = w.detailed_status
  weather = weather[0].upper() + weather[1:]
  currTemp = w.temperature('celsius')
  humid = w.humidity
  wind = observation.weather.wind()
  cloud = w.clouds      
  windspeed = wind['speed']
  w = wind['deg']
  if w >=337.5 or w<=22.5:
      d="N"
  elif w<=67.5:
      d = "NE"
  elif w<=112.5:
      d = "E"
  elif w<=157.5:
      d = "SE"
  elif w<=202.5:
      d = "S"
  elif w<=247.5:
      d = "SW"
  elif w<=292.5:
      d = "W"
  else:
      d = "NW"
  

  # Draw the weather state at the top.
  drawText(weather, 60, 20, 15, white)
    
  # Show the weather icon
  renderWeatherIcon(icon, 20, 80, 250, 250)

  # Show the headline figures to the right.
  y = 85
  drawText("Temperature: " + str(int(currTemp['temp'])) + "C", 45, 320, y, white)
  y += 50
  drawText("Humidity: " + str(humid) + "%", 45, 320, y, white)
  y += 50
  drawText("Wind: " + d + ", " + str(windspeed) + "m/s", 45, 320, y, white)
  y += 50
  drawText("Cloud: " + str(cloud) + "%", 45, 320, y, white)
  y += 50
  drawText("Sunrise: " + srise, 45, 320, y, white)
  y += 50
  drawText("Sunset: " + sset, 45, 320, y, white)

  # Time and date at the bottom
  theTime = str(datetime.datetime.now().time())
  theDate = time.strftime("%d/%m/%Y")
  drawText(theTime[0:5] + ", " + theDate,60,20,390, white)

  # Paint the screen
  pygame.display.update()
  #except:
  #  print("Problems!")
  #  print("Weather error:", sys.exc_info()[0])
  #  print("Weather error:", sys.exc_info()[1])
      
def renderWeather(): 
  # Renders longer-term weather onto the display
  observation = mgr.weather_at_place('Market Deeping,uk')
  w = observation.weather
  currTemp = w.temperature(unit='celsius')
  #icon = w.weather_icon_name

  sunrise_iso = weather.sunrise_time(timeformat='iso')
  sunrset_iso = weather.sunset_time(timeformat='iso')

  one_call = mgr.one_call(lat=52.6796, lon=-0.3216) # Market Deeping still.
  theTemp = one_call.current.temperature()

  # Get the weather for the next few hours...
  temps = []
  humidity = []
  wind = []
  for n in range(5):
      temps.append(one_call.forecast_hourly[n].temperature('celsius').get())
      wind.append(one_call.forecast_hourly[0].wind().get('speed', 0))
      humidity.append(one_call.forecast_hourly[n].temperature('celsius').get('feels_like_night', None))

  # Get the daytime and nighttime temperatures for the next 5 days.
  mornTemps = []
  eveTemps = []
  for n in range(5):
      dayTemps.append(one_call.forecast_daily[n].temperature('celsius').get('feels_like_day', None))
      nightTemps.append(one_call.forecast_daily[n].temperature('celsius').get('feels_like_night', None))
  
  
  # Do the 3-hourly forecast...
  hourlyFc = owm.three_hours_forecast('Market Deeping,uk')
  f = hourlyFc.forecast
  lst = f.weathers

  pygame.draw.rect(lcd, grey, (0, 95, 320, 73))
  x=15
  for weather in lst:
    if x < 300:
      icon = weather.weather_icon_name
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
        theTemp = int(weather.get_temperature(unit='celsius')['day'])
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
  #except:
  ## Weather trouble...
  #print ("Weather error:", sys.exc_info()[0])
  #print ("Weather error:", sys.exc_info()[1])
  #drawText("Weather unavailable",20, 5, 5)
  #pygame.display.update()

    
def renderWeatherIcon(icon, xPos, yPos, xSize=90, ySize=90):
  # Renders a weather icon onto the display
  #image_url = "http://openweathermap.org/img/w/" + icon + ".png"
  image_url = "http://openweathermap.org/img/wn/" + icon + "@2x.png"
  image_str = urlopen(image_url).read()
  image_file = io.BytesIO(image_str)
  image = pygame.image.load(image_file)
  image = pygame.transform.scale(image, [xSize,ySize])
  lcd.blit(image, (xPos, yPos))

def showBriefWeather():
    observation = mgr.weather_at_place('Market Deeping,uk')
    w = observation.weather
    currTemp = w.temperature(unit='celsius')
    icon = w.weather_icon_name
    renderWeatherIcon(icon, 60, 90, 300, 300)
    drawText(str(int(currTemp['temp'])) + "C", 175, 390, 150, white)
    pygame.display.update()

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


def showAnaTime(howLong):
  # howLong is how long to render the time like this before returning to the main loop.

  for x in range(howLong * 100):
    #Draw an analgoue representation. 720 x 480
    theTime = datetime.datetime.now()
    tDay = theTime.day
    tHour = theTime.hour
    tMin = theTime.minute
    tSeconds = theTime.second
    tMilli = int(theTime.microsecond / 1000)
    dayNum = datetime.datetime.today().weekday()
    days = {0:'MON', 1:'TUE', 2:'WED', 3:'THU', 4:'FRI', 5:'SAT', 6:'SUN'}
    
    xCentre = 800 / 2
    yCentre  = 480 / 2
    lcd.fill(black)

    # Draw the little tick-marks
    for mark in range(60):
      tickStart = 185
      tickLength = 15
      # Trig is CPU heavy. Calculate once, use twice.
      cosCalc = math.cos((270 + 6 * mark) * 3.14159 / 180)
      sinCalc = math.sin((270 + 6 * mark) * 3.14159 / 180)
      xCoordStart = int(xCentre + tickStart * cosCalc)
      yCoordStart = int(yCentre + tickStart * sinCalc)
      xCoordEnd = int(xCentre + (tickStart + tickLength) * cosCalc)
      yCoordEnd = int(yCentre + (tickStart + tickLength) * sinCalc)
      if mark % 5 == 0:
        pygame.draw.line(lcd, white, [xCoordStart, yCoordStart], [xCoordEnd, yCoordEnd], 5)
      else:
        pygame.draw.aaline(lcd, white, [xCoordStart, yCoordStart], [xCoordEnd, yCoordEnd], 1)

    # Show date and day
    drawText(days[dayNum], 30, int(xCentre) + 70, int(yCentre) - 18, white)
    drawText(str(tDay), 30, int(xCentre) + 135, int(yCentre) - 18, red)
    
    # Hour hand.
    hourHandLength = 110
    if tHour > 12:
      tHour = tHour - 12
      
    hourAngle=(tHour * 30) + (tMin * 0.5) + 270
    # Hour hand made from a thin line, a circle, a thick line, then a circle.
    cosCalc = math.cos(hourAngle * 3.14159 / 180)
    sinCalc = math.sin(hourAngle * 3.14159 / 180)

    # Thin line
    xCoordStart = int(xCentre)
    yCoordStart = int(yCentre)
    xtCoordEnd = int(xCentre + (hourHandLength * 0.35) * cosCalc)
    ytCoordEnd = int( yCentre + (hourHandLength * 0.35) * sinCalc)
    pygame.draw.line(lcd, white, [xCoordStart, yCoordStart], [xtCoordEnd, ytCoordEnd], 7)

    
    # Thick line
    xCoordEnd = int(xCentre + hourHandLength * cosCalc)
    yCoordEnd = int(yCentre + hourHandLength * sinCalc)
    pygame.draw.line(lcd, white, [xtCoordEnd, ytCoordEnd], [xCoordEnd, yCoordEnd], 15)    

    # Inner-most circle
    pygame.draw.circle(lcd, white, [int(xtCoordEnd), int(ytCoordEnd)], 6, 0)

    # Outer-most circle
    pygame.draw.circle(lcd, white, [int(xCoordEnd), int(yCoordEnd)], 6, 0)

    # ################
    # Minute hand. 
    minHandLength = 184
    cosCalc = math.cos((270 + (6 * tMin) + (0.1 * tSeconds)) * 3.14159 / 180)
    sinCalc = math.sin((270 + (6 * tMin) + (0.1 * tSeconds)) * 3.14159 / 180)

    # Thin line
    xCoordStart = int(xCentre)
    yCoordStart = int(yCentre)
    xtCoordEnd = int(xCentre + (minHandLength * 0.2) * cosCalc)
    ytCoordEnd = int(yCentre + (minHandLength * 0.2) * sinCalc)
    pygame.draw.line(lcd, black, [xCoordStart, yCoordStart], [xtCoordEnd, ytCoordEnd], 9)
    pygame.draw.line(lcd, white, [xCoordStart, yCoordStart], [xtCoordEnd, ytCoordEnd], 7)

    
    # Thick line 
    xCoordEnd = int(xCentre + minHandLength * cosCalc)
    yCoordEnd = int(yCentre + minHandLength * sinCalc)
    pygame.draw.line(lcd, black, [xtCoordEnd, ytCoordEnd], [xCoordEnd, yCoordEnd], 17)
    pygame.draw.line(lcd, white, [xtCoordEnd, ytCoordEnd], [xCoordEnd, yCoordEnd], 15)

    # Inner-most circle
    pygame.draw.circle(lcd, white, [int(xtCoordEnd), int(ytCoordEnd)], 6, 0)
    
    # Outer-most circle
    pygame.draw.circle(lcd, white, [int(xCoordEnd), int(yCoordEnd)], 6, 0)

    # Circle dead-centre to hide the centre-point ends of the lines.
    pygame.draw.circle(lcd, white, [int(xCentre), int(yCentre)], 15, 0)
  
    # Second hand.
    secHandLength = 200
    secAngle = (6 * tSeconds) + (0.006 * tMilli)
    xCoord = int(xCentre + secHandLength * math.cos((270 + secAngle) * (3.14159 / 180)))
    yCoord = int(yCentre + secHandLength * math.sin((270 + secAngle) * (3.14159 / 180)))
    pygame.draw.line(lcd, red, [int(xCentre), int(yCentre)], [int(xCoord), int(yCoord)], 5)
    # Add a little stubby line in the opposite direction, like on a watch
    xCoord = int(xCentre + (secHandLength / 7) * math.cos((90 + secAngle) * (3.14159 / 180)))
    yCoord = int(yCentre + (secHandLength / 7) * math.sin((90 + secAngle) * (3.14159 / 180)))
    pygame.draw.line(lcd, red, [int(xCentre), int(yCentre)], [xCoord, yCoord], 5)
    
    pygame.draw.circle(lcd, red, [int(xCentre), int(yCentre)], 10, 0)
    pygame.draw.circle(lcd, black, [int(xCentre), int(yCentre)], 2, 0)
  
    # Add date and render.
    theDate = time.strftime("%d/%m/%Y")
    drawText(theDate, 50, 5, int(yCentre) + 175, white)
    pygame.display.update()
    time.sleep(0.01)


def drawQuoteText(surface, text, color, rect, font=None, aa=False, bkg=None, fntSize=50):
    rect = pygame.Rect(rect)
    y = rect.top
    lineSpacing = -2
    pygame.font.init()

    font = pygame.font.Font(font, fntSize)

    # get the height of the font
    fontHeight = font.size("Tg")[1]
    
    while text:
        i = 1
        # determine if the row of text will be outside our area
        if y + fontHeight > rect.bottom:
            return text   # was break. 
        
        # determine maximum width of line
        while font.size(text[:i])[0] < rect.width and i < len(text):
            i += 1

        # if we've wrapped the text, then adjust the wrap to the last word
        if i < len(text):
            i = text.rfind(" ", 0, i) + 1

        # render the line and blit it to the surface
        if bkg:
            image = font.render(text[:i], 1, color, bkg)
            image.set_colorkey(bkg)
        else:
            image = font.render(text[:i], aa, color)

        surface.blit(image, (rect.left, y))
        y += fontHeight + lineSpacing

        # remove the text we just blitted
        text = text[i:]

    return text

def showLitTime(howLong = 15):
    global quotes

    # Pick up the time
    theTime = datetime.datetime.now()
    tHour = theTime.hour
    tMin = theTime.minute

    if tHour < 10:
        tHr = "0" + str(tHour)
    else:
        tHr = str(tHour)

    if tMin < 10:
        tMn = "0" + str(tMin)
    else:
        tMn = str(tMin)
        
    #f= open("/home/pi/lit.txt","a")
    #f.write("Looking for" + tHr + ':' + tMn + "\n")
    #f.close()
    #print ("Looking for" + tHr + ':' + tMn)

    # Find all the times that are available, and pick one
    # If there's no entry for that time, jump forward a minute and try that.
    timeOptions = []
    gotOne = False
    while gotOne == False:
        for entry in quotes:
            if  entry[0] == tHr + ':' + tMn:
                timeOptions.append(entry)
                gotOne = True

        if gotOne == False:
            tMin += 1
            if tMin>59:
                tMin = 0
                tHour += 1

                if tHour > 23:
                    tHour=0
                    
            if tHour < 10:
                tHr = "0" + str(tHour)
            else:
                tHr = str(tHour)

                if tMin < 10:
                    tMn = "0" + str(tMin)
                else:
                    tMn = str(tMin)
            
    # Now select (at random) one of the quotes for this time.
    whichQuote = random.randint(0, len(timeOptions) -1)
    
    quoteHighlight = timeOptions[whichQuote][1]
    quoteText = timeOptions[whichQuote][2]
    quoteTitle = timeOptions[whichQuote][3]
    quoteAuthor = timeOptions[whichQuote][4]
                
    # Render to page. (720x480 total area)
    fontPath = '/usr/share/fonts/truetype/'
    trySize = 100

    leftovers = drawQuoteText(lcd, quoteText, white, [10,10,710, 370], fontPath + 'liberation2/LiberationSerif-Italic.ttf', False, None, trySize)

    while leftovers != '' and trySize >=10:
        trySize -= 5
        leftovers = drawQuoteText(lcd, quoteText, white, [10,10,710, 370], fontPath + 'liberation2/LiberationSerif-Italic.ttf', False, None, trySize)

    # Same thing again for the book title. Should put this into a function, really.
    tryTSize = 50
    titleLeftovers = drawQuoteText(lcd, quoteTitle, white, [15, 360, 700, 50], fontPath + 'liberation2/LiberationSans-Bold.ttf', False, None, tryTSize)
    
    while titleLeftovers != '' and tryTSize >=10:
        tryTSize -= 3
        titleLeftovers = drawQuoteText(lcd, quoteTitle, white, [15, 360, 700, 50], fontPath + 'liberation2/LiberationSans-Bold.ttf', False, None, tryTSize)

    # f= open("/home/pi/lit.txt","a")
    # f.write("Done - trySize is " + str(trySize)  + ". Rendering quote to display \n")
    # f.close()
    lcd.fill(black)

    # If the time part is in the first half, draw the whole text white, then again (up to the time) in red to cover it.
    # Some of the excerpts are capitalised and others aren't.
    qText = quoteText.upper()
    qHighlight = quoteHighlight.upper()
    
    if qText.find(qHighlight) < len(quoteText) / 2:
        drawQuoteText(lcd, quoteText, white, [10,10,710, 370], fontPath + 'liberation2/LiberationSerif-Italic.ttf', False, None, trySize)
        newtext = quoteText.find(quoteHighlight)  + len(quoteHighlight)
        drawQuoteText(lcd, quoteText[:newtext], red, [10,10,710, 370], fontPath + 'liberation2/LiberationSerif-Italic.ttf', False, None, trySize)
    elif qText.find(qHighlight) >= len(quoteText) / 2:
        drawQuoteText(lcd, quoteText, red, [10,10,710, 370], fontPath + 'liberation2/LiberationSerif-Italic.ttf', False, None, trySize)
        newtext = quoteText.find(quoteHighlight)  # + len(quoteHighlight)
        drawQuoteText(lcd, quoteText[:newtext], white, [10,10,710, 370], fontPath + 'liberation2/LiberationSerif-Italic.ttf', False, None, trySize)
    else:
        # Quote highlight can't be found
        drawQuoteText(lcd, quoteText, white, [10,10,710, 370], fontPath + 'liberation2/LiberationSerif-Italic.ttf', False, None, trySize)

    #pygame.draw.rect(lcd, yellow, (15, 360, 695, 57))
    drawQuoteText(lcd, quoteTitle, grey, [15, 360, 710, 417], fontPath + 'liberation2/LiberationSans-Bold.ttf', False, None, tryTSize)
    #drawText(quoteTitle, 45, 15, 360, grey)
    drawText(quoteAuthor, 45, 15, 415, white)
    #drawQuoteText(lcd, quoteTitle[:25], white, [10,360,710, 390], fontPath + 'liberation2/LiberationSerif-Bold.ttf', False, None, tryTSize)
    #drawQuoteText(lcd, quoteAuthor, white, [10,415,710, 470], fontPath + 'liberation2/LiberationSerif-Regular.ttf')
    pygame.display.update()    
    time.sleep(howLong)

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
time.sleep(10)

def main():    
  global whatsOn
  global weatherStyle
  global sunrise
  global sunset
  backlight = Backlight()
  backlight.fade_duration = 2
  
  whichHeadline = 0
  lcd.fill(white)
  
  while True:
    # Set screen brightness....
    now = datetime.datetime.now()
    hr = now.hour

    # EXPERIMENT FOR ADAPTIVE RIGHTNESS
    #if hr > 12:
    #    t = sunset - now
    #    minutes = t.total_seconds() / 60

    #    if minutes <= 50 and minutes >= -45:
    #        bright = 100 - (50 - minutes)
    #    elif minutes > -45:
    #        bright = 5
    #    else:
    #        bright = 100
    #else:
    #    t = sunrise - now
    #    minutes = t.total_seconds() / 60

    #    if minutes <= 45 and minutes >= -50:
    #        bright = 50 - minutes
    #    elif mintutes > -50:
    #        bright = 100
    #    else:
    #        bright = 5

    if hr == 6:
      backlight.brightness = 25
    elif hr == 21:
      backlight.brightness = 50
    elif hr >= 22 or hr < 7:
      backlight.brightness = 5
    else:
      backlight.brightness = 100
      
    # Show weather
    whatsOn = 'weather'
    lcd.fill(black)

    try:
      weatherStyle = "normal"
      
      if weatherStyle == 'normal':
        renderWeatherNow()
      elif weatherStyle == 'brief':
        # icon only view
        showBriefWeather()
      else:
        # Detailed view
        renderWeather()

      time.sleep(15)
    except:
      time.sleep(0.25)

    # Show the clock
    whatsOn = 'clock'
    if clockStyle == 'analogue':  
        showAnaTime(15)
    else:
        # Show digital clock
        whatsOn = 'clock'
        lcd.fill(black)
        for n in range(30):
            showTime()
            time.sleep(0.01)
            lcd.fill(black)    
                
    # Show the news...
    whatsOn='news'
    try:
      lcd.fill(black)
      renderNews()
      time.sleep(10)
    except:
      print ("Unexpected error:", sys.exc_info()[0])         
      print ("Unexpected error:", sys.exc_info()[1])
      time.sleep(0.25)

    # Show the clock
    whatsOn = 'clock'
    if clockStyle == 'analogue':  
        showAnaTime(15)
    else:
        # Show digital clock
        whatsOn = 'clock'
        lcd.fill(black)
        for n in range(30):
            showTime()
            time.sleep(0.01)
            lcd.fill(black)    

    # Always have the literature clock in the rotation.
    whatsOn = 'clock'
    showLitTime(15)

    #pygame.event.get()
    
main()

if __name__ == '__main__':
  try:
    main()
  except KeyboardInterrupt:
    pass
  finally:
    pygame.quit()   # stops the PyGame engine
    sys.exit()
