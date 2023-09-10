#Dependencies
import os
import disnake
import random
import json
import re
import asyncio
from dotenv import load_dotenv
from disnake.ext import commands
from disnake import utils
from disnake import TextInputStyle

#Creating connenction to discord
load_dotenv()
intents = disnake.Intents.default()
intents.message_content = True
intents.members = True
token = os.getenv('DISCORD_TOKEN')
bot = commands.Bot(command_prefix='/', intents=intents, case_insensitive=True)

#Code that runs when bot first runs
@bot.event
async def on_ready():
    print(f'{bot.user.name} has connencted to Discord!')

#Takes two lists and returns true if they share any elements
def compareLists(list1, list2):
    for i in list1:
        if str(i) in list2:
            return True
    return False

#Code for making the inventory string
def inventoryString(inventory):
    string = f'```Coins: {inventory["coins"]} [{inventory["bonus"]}%]\nInventory: '
    for i in range(len(inventory["items"])):
        string += inventory["items"][i]
        if i != len(inventory["items"]) - 1:
            string += ", "
    string += "\nStatuses: "
    for i in range(len(inventory["statuses"])):
        string += inventory["statuses"][i]
        if i != len(inventory["statuses"]) - 1:
            string += ", "
    string += "\nEffects: "
    for i in range(len(inventory["effects"])):
        string += inventory["effects"][i]
        if i != len(inventory["effects"]) - 1:
            string += ", "
    string += "\nImmunities: "
    for i in range(len(inventory["immunities"])):
        string += inventory["immunities"][i]
        if i != len(inventory["immunities"]) - 1:
            string += ", "
    for k, v in inventory.items():
        if k not in ("coins", "bonus", "items", "statuses", "effects", "id", "immunities", "vote"):
            string += f'\n{k}: '
            for i in range(len(v)):
                string += v[i]
                if i != len(v) - 1:
                    string += ", "
    string += "\nVote(s): "
    for i in range(len(inventory["vote"])):
        string += inventory["vote"][i]
        if i != len(inventory["vote"]) - 1:
            string += ", "
    string += "```"
    return string

#Code for managing inventories
@bot.command(aliases=['inventory', 'inv'], help='')
async def inventories(ctx, arg1="", *arg2):
    #Getting discord roles
    for role in ctx.guild.roles:
        if role.name == "Participant":
            participantRole = role
    for role in ctx.guild.roles:
        if role.name == "Dead":
            deceasedRole = role
    
    channel = ctx.channel
    allowed = "Bluedetroyer"
    gameMembers = []
    for x in channel.members:
        if compareLists(x.roles, ["Participant", "Deceased"]) and (not compareLists(x.roles, ["Master", "Host", "Co-Host", "True Deceased"])):
            gameMembers.append(x)
    if len(gameMembers) == 1:
        allowed = gameMembers[0].name
    #Authorization check
    if (not compareLists(ctx.author.roles, ["Master", "Host", "Co-Host"]) and not (ctx.author in channel.members)):
        await ctx.send("You don't have permession to edit inventories in this channel")
        return
    #Creating inventory
    if arg1.lower() == "create":
        file = open("inventoryinfo.json")
        data = json.load(file)
        file.close()
        if channel.name in data:
            await ctx.send("There's already an inventory for that channel. Please delete/forget it if you want to make a new one")
            return
        newInventory = {"coins": 0, "bonus": 0, "items": [], "statuses": [], "effects": [], "immunities": [], "vote": []}
        inventoryId = await channel.send(inventoryString(newInventory))
        newInventory["id"] = inventoryId.id
        data[channel.name] = newInventory
        file = open("inventoryinfo.json", "w")
        file.write(json.dumps(data, indent=4))
        file.close()
    #Editing coins/coin bonus
    elif arg1.lower() in ("coins", "coin", "bonus"):
        if arg1.lower() == "coin":
            arg1 = "coins"
        file = open("inventoryinfo.json")
        data = json.load(file)
        file.close()
        inventory = data[channel.name]
        message = await channel.fetch_message(inventory["id"])
        amount = int(arg2[1])
        if arg2[0].lower() in ("remove", "subtract", "delete"):
            amount *= -1
        if arg2[0].lower() in ("remove", "subtract", "delete", "add"):
            inventory[arg1.lower()] += amount
        elif arg2[0].lower() == "set":
            inventory[arg1.lower()] = amount
        await message.edit(content=inventoryString(inventory))
        file = open("inventoryinfo.json", "w")
        file.write(json.dumps(data, indent=4))
        file.close()
    #Editing items/statuses/effects
    elif arg1.lower() in ("items", "statuses", "effect", "effects", "item", "status", "immunities", "immunity", "vote", "votes"):
        if arg1.lower() == "item":
            arg1 = "items"
        if arg1.lower() == "status":
            arg1 = "statuses"
        if arg1.lower() == "immunity":
            arg1 = "immunities"
        if arg1.lower() == "effect":
            arg1 = "effects"
        if arg1.lower() == "votes":
            arg1 = "vote"
        file = open("inventoryinfo.json")
        data = json.load(file)
        file.close()
        inventory = data[channel.name]
        message = await channel.fetch_message(inventory["id"])
        if arg2[0].lower() == "add":
            for thing in arg2[1:]:
                inventory[arg1.lower()].append(thing)
        elif arg2[0].lower() == "remove":
            for thing in arg2[1:]:
                for item in inventory[arg1.lower()]:
                    if item.lower() == thing.lower():
                        inventory[arg1.lower()].remove(item)
                        break
        elif arg2[0].lower() == "clear":
            inventory[arg1.lower()].clear()
        elif arg2[0].lower() == "set":
            inventory[arg1.lower()].clear()
            for thing in arg2[1:]:
                inventory[arg1.lower()].append(thing)
        await message.edit(content=inventoryString(inventory))
        file = open("inventoryinfo.json", "w")
        file.write(json.dumps(data, indent=4))
        file.close()

        
    #Deletes the inventory message from the channel and removes it from the json file
    elif arg1.lower() == "delete":
        file = open("inventoryinfo.json")
        data = json.load(file)
        file.close()
        inventory = data[channel.name]
        message = await channel.fetch_message(inventory["id"])
        data.pop(channel.name)
        await message.delete()
        file = open("inventoryinfo.json", "w")
        file.write(json.dumps(data, indent=4))
        file.close()
    #Removes the inventory from the json file but leaves the message
    elif arg1.lower() == "forget":
        file = open("inventoryinfo.json")
        data = json.load(file)
        file.close()
        data.pop(channel.name)
        file = open("inventoryinfo.json", "w")
        file.write(json.dumps(data, indent=4))
        file.close()
    #Prints a copy of the inventory that doesn't get updated
    elif arg1.lower() == "send":
        file = open("inventoryinfo.json")
        data = json.load(file)
        file.close()
        inventory = data[channel.name]
        await ctx.send(content=inventoryString(inventory))
    elif arg1.lower() == "refresh":
        file = open("inventoryinfo.json")
        data = json.load(file)
        file.close()
        inventory = data[channel.name]
        message = await ctx.send(content=inventoryString(inventory))
        data[channel.name]["id"] = message.id
        file = open("inventoryinfo.json", "w")
        file.write(json.dumps(data, indent=4))
        file.close()
    elif arg1.lower() == "section":
        file = open("inventoryinfo.json")
        data = json.load(file)
        file.close()
        inventory = data[channel.name]
        message = await channel.fetch_message(inventory["id"])
        if arg2[0].lower() in ("create", "add"):
            inventory[arg2[1]] = []
        if arg2[0].lower() == "remove":
            inventory.pop(arg2[1])
        await message.edit(content=inventoryString(inventory))
        file = open("inventoryinfo.json", "w")
        file.write(json.dumps(data, indent=4))
        file.close()
    #Invalid arguments
    elif arg1 == "":
        await ctx.send("No argument found")
    else:
        file = open("inventoryinfo.json")
        data = json.load(file)
        file.close()
        inventory = data[channel.name]
        message = await channel.fetch_message(inventory["id"])
        if arg1 in inventory:
            if arg2[0].lower() == "add":
                for thing in arg2[1:]:
                    for item in inventory[arg1]:
                        if item.lower() == thing:
                            inventory[arg1].remove(item)
                    inventory[arg1].append(thing)
            elif arg2[0].lower() == "remove":
                for thing in arg2[1:]:
                    for item in inventory[arg1]:
                        if item.lower() == thing.lower():
                            inventory[arg1].remove(item)
                            break
            elif arg2[0].lower() == "clear":
                inventory[arg1].clear()
            elif arg2[0].lower() == "set":
                inventory[arg1].clear()
                for thing in arg2[1:]:
                    inventory[arg1].append(thing)
            await message.edit(content=inventoryString(inventory))
            file = open("inventoryinfo.json", "w")
            file.write(json.dumps(data, indent=4))
            file.close()
        else:
            await ctx.send("Argument " + arg1 + " not recognized for inventory")
