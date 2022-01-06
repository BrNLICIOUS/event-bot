# bot.py

from datetime import date
from datetime import datetime
from discord import embeds, guild, message, user
from discord.channel import CategoryChannel
from discord.ext import commands
from dateutil.relativedelta import relativedelta
import os
import discord
import datetime
import re
import random
import sys
import mysql.connector as database
import aiocron
from mysql.connector.utils import print_buffer

varCategoryName = os.environ['botCategoryName']
varCalendarChannelID = int(os.environ['botCalendarChannelID'])
varMediaChannelName = os.environ['botMediaChannelName']
varBotLogID = int(os.environ['botLogChannelID'])
varGuildID = int(os.environ['botGuildID'])
TOKEN = os.environ['botTOKEN']
varDebug = os.environ['setDebug']
if varDebug == 'True':
    varDebug = True

client = commands.Bot(command_prefix = '.',intents =discord.Intents.all())

## Connect to database
try:
    connection = database.connect(
        user="root",
        password="root",
        host="db",
        port=3306,
        database="bot"
    )
except database.Error as e:
    print(f"Error connecting to MariaDB Platform: {e}")
    sys.exit(1)

# Get Cursor
cursor = connection.cursor()
createTable = "CREATE TABLE IF NOT EXISTS events (eventname CHAR(128), eventdate CHAR(35), channelid CHAR(128), messageid CHAR(128));"
cursor.execute(createTable)
connection.commit()

# Function that allows adding events to database
def add_data(eventname, eventdate, channelid, messageid):
    try:
        statement = "INSERT INTO events (eventname,eventdate,channelid,messageid) VALUES (%s,%s,%s,%s)"
        data = (eventname, eventdate, channelid, messageid)
        cursor.execute(statement, data)
        connection.commit()
        print("Successfully added entry to database")
    except database.Error as e:
        print(f"Error adding entry to database: {e}")


### Joins the bot
@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')
    if varDebug is True:
        print(f'Debugging enabled')
        print(f'Using GuildID: ' + str(varGuildID) + ' Type ' + str(type(varGuildID)))
        print(f'Using CategoryName: ' + str(varCategoryName) + ' Type ' + str(type(varCategoryName)))
        print(f'Using CalenderChannelID: ' + str(varCalendarChannelID) + ' Type ' + str(type(varCalendarChannelID)))
        print(f'Using Token: ' + str(TOKEN) + ' Type ' + str(type(TOKEN)))

    else:
        print(f'Debugging is disabled')
    global guild
    guild = client.get_guild(varGuildID)

@client.event
async def on_message(message):
    formats = ['jpg', 'png', 'gif', 'svg']
    attachments = [f for f in message.attachments if f.filename.split('.')[-1] in formats]
    if message.channel.name == varMediaChannelName and not attachments:
        await message.delete()

### create an event
@client.command()
async def create(ctx,channelName=None,eventDate=None,eventHour=None,eventDescription=None ):
    # user=client.get_user()

    guild = ctx.guild
    categoryName = varCategoryName
    one_month = datetime.datetime.now() + relativedelta(months=1)

    #Specific channel ID to post events in
    calendarChannel = client.get_channel(varCalendarChannelID)

    #Set the category for the bot to create channels to
    category = discord.utils.get(ctx.guild.categories, name=categoryName)
    

    try:
        statement = "SELECT eventdate, eventname FROM events"
        cursor.execute(statement)
        record = cursor.fetchall()


        #Check if all the variables are filled
        if channelName is None:
            await ctx.channel.send("Please enter an event name ---> **.create \"eventname\" \"date\" \"hour\"**")
            return
        elif eventDate is None:
            await ctx.channel.send("Please choose a date in DD-MM-YYYY format  ---> **.create \"eventname\" \"date\" \"hour\"**")
            return
        elif eventHour is None:
            await ctx.channel.send("Please choose an hour in 24 hour format ---> **.create \"eventname\" \"date\" \"hour\"**")
            return
        elif eventDescription is None:
            eventDescription=" "
        

        #Check if the date in the eventDate is the correct format
        try:
            datetime.datetime.strptime(eventDate, '%d-%m-%Y')
        except ValueError:
            await ctx.channel.send("Incorrect data format, should be DD-MM-YYYY")
            raise ValueError("Incorrect data format, should be DD-MM-YYYY")

        # Only allow events to be created a max of 1 month in the future to prevent spamming
        if datetime.datetime.strptime(eventDate, '%d-%m-%Y') > one_month:
            await ctx.channel.send("Only events up to 1 month in the future are allowed")
            return

        if datetime.datetime.strptime(eventDate, '%d-%m-%Y') < datetime.datetime.now() - datetime.timedelta(days=1):
            await ctx.channel.send("Can not create an event in the past")
            return

        for row in record:
            if datetime.datetime.strptime(eventDate, '%d-%m-%Y') == datetime.datetime.strptime(row[0], '%d-%m-%Y') and str(channelName) == str(row[1]):
                await ctx.channel.send("An event with this name and date already exists, if it is not the same event please give this event a different name")
                return

          
            # Check if 24 hour format is used"
            regex = "^([01]?[0-9]|2[0-3]):[0-5][0-9]$"
            p = re.compile(regex)

            if (eventHour == "") :
                await ctx.channel.send("Set an event time in 24 hour format")
                return 
            m = re.search(p, eventHour)

            if m is None :
                await ctx.channel.send("Set an event time in 24 hour format")
                return 

        colorValue = random.randint(0, 0xffffff)
        mbed = discord.Embed(
            title = "📅  " + channelName + " - " + eventDate + " - " + eventHour + " UTC",
            description = eventDescription,
            colour = colorValue,
        )
        mbed.set_footer(text="Created by " + ctx.message.author.display_name)
        mbed.add_field(name="Attendees", value="-", inline=True)

        
        #Create new channel if all else succeeded
        newChannel = await guild.create_text_channel(name='{}'.format(channelName),category=category)
        newEvent = await calendarChannel.send(embed=mbed)
        message = newEvent.id
        message = await calendarChannel.fetch_message(newEvent.id)
        await message.add_reaction("\U00002705")

        #Create role for the channel
        newRole = await guild.create_role(name=channelName,mentionable=True)
        await newChannel.set_permissions(newRole, read_messages=True, send_messages=True, read_message_history=True,add_reactions=True,use_external_emojis=True)

        print(newChannel)
        add_data(channelName, eventDate, newChannel.id, newEvent.id)


    except database.Error as e:
        print(f"Error retrieving entry from database: {e}")
        sys.exit()

## Run every 1 minutes --> Only advised in DEV mode
#@aiocron.crontab('*/1 * * * *')

# run a cleanup at 09:00
#@aiocron.crontab('0 9 * * *')
# run a cleanup at 06:00
@aiocron.crontab('0,30 6 * * *')

async def cronjob1():
    # A channel to keep track of the cleanup
    channel = client.get_channel(varBotLogID)
    await channel.send('Running cleanup')
    # The category in discord with all the text channels
    textChannel = discord.utils.get(guild.text_channels, name=varCategoryName)


    try:
        statement = "SELECT eventdate, channelid, messageid, eventname FROM events"
        cursor.execute(statement)
        record = cursor.fetchall()
        for row in record:
            # Cleanup if the date is older than today (only checks the date not hour)
            if datetime.datetime.strptime(row[0], '%d-%m-%Y') < datetime.datetime.now() - datetime.timedelta(days=1):
                     

                for textChannel in guild.text_channels:
                    if int(textChannel.id) == int(row[1]):
                        print("deleting", row[1])
                        await textChannel.delete()
                        print("deleting message with id", row[2])
                        # Delete the embed message in the events-signup channel
                        await client.http.delete_message(varCalendarChannelID, int(row[2]))
                        await channel.send("deleted event "+ row[3])


                        
                        role_object = discord.utils.get(guild.roles, name=row[3])
                        if role_object in guild.roles: # Check if role is in the guild
                            print('deleting role', row[3])
                            await role_object.delete()

                        channelid = str(row[1])
                        deleteQuery = """DELETE FROM bot.events WHERE channelid=%s;"""
                        tuple1 = (channelid,)
                        cursor.execute(deleteQuery,tuple1)
                        connection.commit()
                        print("Deleted record with channelid",row[1]," from the database")

    except database.Error as e:
        print(f"Error retrieving entry from database: {e}")
        sys.exit()




@client.event
async def on_raw_reaction_add(payload):


## Grant the role when you click on the checkmark emoji
    try:
        statement = "SELECT messageid, eventname FROM events"
        cursor.execute(statement)
        record = cursor.fetchall()
        for row in record:
            message_id = payload.message_id
            if message_id == int(row[0]):
                guild_id= payload.guild_id
                guild = discord.utils.find(lambda g : g.id == guild_id, client.guilds)
                emoji = '✅'

                if payload.emoji.name == str(emoji):
                    role = discord.utils.get(guild.roles, name=str(row[1]))
                    member = payload.member

                    if member is not None:
                        await member.add_roles(role)
        
    except database.Error as e:
        print(f"Error retrieving entry from database: {e}")
        sys.exit()


### Edit the embedded message to include the user who clicked on the green checkmark as an attendee
    channel = client.get_channel(payload.channel_id)
    message = await channel.fetch_message(payload.message_id)
    embeds, emojis  = message.embeds[0], '✅'
    embed_dict = embeds.to_dict()
    index = emojis.index(payload.emoji.name)    
    if message.author == payload.member:
        return

    for field in embed_dict["fields"]:
        
        old_value = ""
        old_value = field["value"] + ""
        if str(old_value) == str("-"):
            old_value = ""
        else:
            old_value = field["value"] + "\n"
        if payload.member.mention not in field["value"]:
            new_value = ""
            new_value = old_value + payload.member.mention +"\n"
            embeds.set_field_at(index, name=embeds.fields[index].name, value=new_value, inline=False)   
            await message.edit(embed=embeds)
         





@client.event
async def on_raw_reaction_remove(payload):


## Remove role if the user unchecks the emoji
    try:
        statement = "SELECT messageid, eventname FROM events"
        cursor.execute(statement)
        record = cursor.fetchall()
        for row in record:
            message_id = payload.message_id
            if message_id == int(row[0]):
                guild_id= payload.guild_id
                guild = discord.utils.find(lambda g : g.id == guild_id, client.guilds)
                emoji = '✅'

                if payload.emoji.name == str(emoji):
                    role = discord.utils.get(guild.roles, name=str(row[1]))
                    member = guild.get_member(payload.user_id)

                    if member is not None:
                        await member.remove_roles(role)
    except database.Error as e:
        print(f"Error retrieving entry from database: {e}")
        sys.exit()



### Remove the user from the attendee list if they uncheck the green checkmark

    channel = client.get_channel(payload.channel_id)
    message = await channel.fetch_message(payload.message_id)
    # print(message.content)
    embeds, emojis  = message.embeds[0], '✅'
    embed_dict = embeds.to_dict()
    index = emojis.index(payload.emoji.name)    
    if message.author == payload.member:
        return

    for field in embed_dict["fields"]:
        
        old_value = ""
        old_value = field["value"] + ""
        if str(old_value) == str("-"):
            old_value = ""
        else:
            old_value = field["value"] + "\n"

        member = guild.get_member(payload.user_id)
        if member.mention in old_value:
            new_value = ""
            for line in field["value"].splitlines():
                if member.mention == line:
                    new_value = old_value.replace(line,'')
                    if len(new_value) < 2:
                        new_value = "-"
                    new_value = "".join([s for s in new_value.splitlines(True) if s.strip("\r\n")])

                    embeds.set_field_at(index, name=embeds.fields[index].name, value=new_value, inline=False)   
                    await message.edit(embed=embeds)



client.run(TOKEN)



#mariadb run command:
# docker run --name=mariadb -e MYSQL_ROOT_PASSWORD=root -e MYSQL_DATABASE=bot -p 3306:3306 -d mariadb
#### CREATE TABLE events (eventname CHAR(128), eventdate CHAR(35), channelid CHAR(128), messagid CHAR(128));