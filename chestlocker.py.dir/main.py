import os, pickle
import org.bukkit.block.BlockFace as BlockFace
import org.bukkit.Bukkit as bukkit
import org.bukkit.craftbukkit.entity.CraftPlayer
import org.bukkit.craftbukkit.command.ColouredConsoleSender
from types import *
from datetime import datetime, timedelta

#Copyright Tony Speer

#This is way not finished yet.

debug = 0
settings = dict()
db = dict()

def initalize():
    global debug, db, settings
    settings = loadsettings()
    db = loaddb()

def loadsettings():
    f = open("plugins/chestlocker.cfg")
    settings = dict()
    for i in f.readlines():
        settings['%s' % i.split(":")[0]] = ":".join(i.split("#")[0].split(":")[1:]).rstrip()
    f.close()
    return settings

def loaddb():
    try:
        f = open("plugins/chestlocker.db")
        db = pickle.load(f)
        f.close()
    except IOError:
        print "Chest locker is creating the DB file"
        db = dict(
                chests=[],
                credits=[],
                index=dict()
                )
        savedb(db)
    
    return db

def savedb(db):
    f = open("plugins/chestlocker.db", "w")
    pickle.dump(db, f)
    f.close()

def index(name):
    global db
    
    try:
        return db['index'][name]
    except KeyError:
        db['index']
        savedb(db)
        return 0

def indexIncr(name):
    global db
    count = index(name) + 1
    db['index'][name] = count
    savedb(db)
    return count

class Chest:
    def __init__(self, block):
        self.block = block
        self.chest = self.getChest()
        if self.chest == None:
            self.owner = None
        else:
            self.owner = Player(self.chest['player'])
    
    def getChest(self):
        global db        
        
        for i in db['chests']:
            if (i['x'] == self.block.getX() and i['y'] == self.block.getY() and i['z'] == self.block.getZ() and i['world'] == str(self.block.getWorld().getUID())):
                return i
        
        attached = findAttachedChest(self.block)
        
        if attached != None: #look again to see if the attached chest is locked.
            for i in db['chests']:
                if (i['x'] == attached.getX() and i['y'] == attached.getY() and i['z'] == attached.getZ() and i['world'] == str(attached.getWorld().getUID())):
                    return i
        
        return None
    
    def isLocked(self):
        global settings, debug, db
        
        if type(self.chest) != NoneType and self.chest != None:
            assert type(self.chest) != NoneType
            
            if self.owner.isOverQuota():
                self.unlockChest(self.owner.name)
                self.owner.msg("One of your chests has been unlocked because you are over quota.")
                if debug:
                    print "Remove a chest lock because it user is over quota."
        
        if self.chest == None:
            return 0
        else:
            return 1
    
    def isOwner(self, player):
        if self.chest != None:
            if str(self.owner) == str(Player(player)):
                return 1
        return 0
    
    def lockChest(self, player):
        global db
        self.chest = dict(
                        id = indexIncr("chest"),
                        x = self.block.getX(),
                        y = self.block.getY(),
                        z = self.block.getZ(),
                        player = str(player),
                        world = str(self.block.getWorld().getUID())
                        )
        db['chests'].append(self.chest)
        savedb(db)
    
    def unlockChest(self, player):
        global db
        
        db['chests'].remove(self.chest)
        
        self.chest = None
        
        savedb(db)

class Player:
    def __init__(self, player):
        if type(player) == str or type(player) == unicode:
            self.name = player
            self.b = bukkit.getPlayerExact(self.name) # bukkit class for player
        elif type(player) == org.bukkit.craftbukkit.entity.CraftPlayer:
            self.name = player.getName()
            self.b = player
        elif type(player) == org.bukkit.craftbukkit.command.ColouredConsoleSender:
            self.b = player
            self.name = "Console"
        elif player == Player:
            self.b = player.b
            self.name = player.name
        else:
            print "ERROR: Could not find player", type(player), player
            raise ValueError
        
    def __str__(self):
        return self.name
    
    def msg(self, txt):
        self.b.sendMessage(txt)
    
    def getChests(self):
        global db
        
        out = []
        
        for i in db['chests']:
            if i['player'] == self.name:
                out.append(i)
        
        return out
    
    def chestCount(self):
        return len(self.getChests())
    
    def maxlocks(self): #calculates the max locks a player can have
        global settings
        
        if self.b.hasPermission("chestlocker.unlimited") or int(settings['maxlocks']) == -1:
            return -1
        
        return int(settings['maxlocks']) + len(self.credits())
    
    def addCredit(self, duration = 0):
        global db
        
        expires = 1
        
        if type(duration) == int and duration > 0:
            expiretime = datetime.now() + timedelta(days=duration)
        elif type(duration) == str:
            duration = duration.lower()
            if duration[-1] == "h":
                expiretime = datetime.now() + timedelta(hours=int(duration[0:-1]))
            elif duration[-1] == "d":
                expiretime = datetime.now() + timedelta(days=int(duration[0:-1]))
            elif duration[-1] == "m":
                expiretime = datetime.now() + timedelta(minutes=int(duration[0:-1]))
            elif int(duration) == 0:
                expires = 0
                expiretime = datetime.now()
            else:
                expiretime = datetime.now() + timedelta(days=int(duration))
        else:
            expires = 0
            expiretime = datetime.now()
        
        c = dict(
                id = indexIncr("credit"),
                player = self.name,
                expires = expires,
                expiretime = expiretime
                )
        
        db['credits'].append(c)
        savedb(db)
    
    def credits(self, showall=0):
        global db
        out = []
        for i in db['credits']:
            if i['player'] == self.name:
                if showall or ( datetime.now() < i['expiretime'] or not i['expires'] ): #filter out expired credits
                    out.append(i)
        return out
    
    def isOverQuota(self, willbe = 0):
        if self.maxlocks() == -1:
            return 0
        
        return self.chestCount() + willbe > self.maxlocks()
    
    def showInfo(self):
        if self.isOverQuota():
            self.msg("You are currently over quota.")
        
        self.msg("You have %s locked chest(s)." % self.chestCount())
        
        if self.maxlocks() == -1:
            self.msg("You have unlimited locks.")
        else:
            self.msg("You have %s lock(s)." % self.maxlocks())
        
        self.msg("You have %s credit(s)." % len(self.credits()))

def findAttachedChest(block):
    global debug
    
    for i in [BlockFace.NORTH, BlockFace.EAST, BlockFace.SOUTH, BlockFace.WEST]:
        b = block.getRelative(i, 1)
        
        if str(b.getType()) == "CHEST":
            return b
    
    return None

@hook.enable
def onenable():
    global debug
    print "Chest Locker Pro 3000 Ultra EXTREME EDITION. By Tony Speer"

    if debug:
        print "Chest locker debug mode is on."
        
    initalize()

@hook.event("Player_join", "normal")
def onPlayerJoin(event):
    player = Player(event.getPlayer())
    
    x = player.chestCount()
    
    if x > 0:
        player.msg("You have %s locked chest(s)." % str(x))
        if player.isOverQuota():
            player.msg("You are %s lock(s) over your allowed limit." % (x - player.maxlocks()))
            player.msg("%s lock(s) will be disabled next time they are touched." % (x - player.maxlocks()))
    

@hook.command
def cl(sender, args):
    global settings
    
    player = Player(sender)
    
    if len(args) < 1:
        sender.sendMessage("Chestlock command usage:")
        
        if sender.hasPermission("chestlocker.lock"):
            sender.sendMessage("- lock: locks a chest you are looking at.")
        if sender.hasPermission("chestlocker.unlock"):
            sender.sendMessage("- unlock: unlocks a chest you are looking at.")
        if sender.hasPermission("chestlocker.credit"):
            sender.sendMessage("- credit <User> [time]: Gives a user a credit that optionly expires.")
        if sender.hasPermission("chestlocker.info"):
            sender.sendMessage("- info: Shows how many chests you have and other info.")
        if sender.hasPermission("chestlocker.reload"):
            sender.sendMessage("- reload: Reloads the settings file.")
    elif args[0] == "lock" and sender.hasPermission("chestlocker.lock"):
        if player.isOverQuota(1):
            sender.sendMessage("You are over the max lock quota. Sorry, you can't lock this.")
            return
        
        blocks = sender.getLineOfSight(None, 100)
        if len(blocks) < 1:
            sender.sendMessage("You must look directly at a chest.")
        else:
            if str(blocks[-1].type) == "CHEST":
                chest = Chest(blocks[-1])
                if not chest.isLocked():
                    chest.lockChest(sender.getName())
                    sender.sendMessage("Chest is now locked.")
                else:
                    sender.sendMessage("This chest is already locked.")
            
            else:
                sender.sendMessage("I can't lock this. Try looking at a chest. Dummy.")
    elif args[0] == "unlock" and sender.hasPermission("chestlocker.unlock"):
        blocks = sender.getLineOfSight(None, 100)
        if len(blocks) < 1:
            sender.sendMessage("You must look directly at a chest.")
        else:
            chest = Chest(blocks[-1])
            if chest.isLocked():
                if chest.isOwner(sender):
                    chest.unlockChest(sender)
                    sender.sendMessage("Chest unlocked.")
                else:
                    sender.sendMessage("You do not own this chest. You can't unlock it.")
            else:
                sender.sendMessage("This chest is not locked.")
    elif args[0] == "info" and sender.hasPermission("chestlocker.info"):
        player.showInfo()
        
        if sender.hasPermission("chestlocker.globalinfo"):
            player.msg("There are currently %s chests in the database." % len(db['chests']))
            
    elif args[0] == "credit" and sender.hasPermission("chestlocker.credit"):
        player = Player(sender)
        if len(args) >= 3:
            p = Player(args[1])
            p.addCredit(args[2])
            sender.sendMessage("Gave %s a credit." % p.name)
        else:
            sender.sendMessage("Missing something?")
    elif args[0] == "reload" and sender.hasPermission("chestlocker.reload"):
        player.msg("Reloading chestlocker.")
        initalize()
        player.msg("Finished.")

@hook.event("block_break", "high")
def onBlockBreak(event):
    global debug
    
    block = event.getBlock()
    
    if str(block.type) == "CHEST":
        chest = Chest(block)
        if chest.isLocked():
            event.setCancelled(True)
            event.getPlayer().sendMessage("This chest is locked. You can't break it.")

@hook.event("block_damage", "high")
def onBlockDamange(event):
    global debug
    
    block = event.getBlock()
    
    if str(block.type) == "CHEST":
        chest = Chest(block)
        if chest.isLocked():
            event.setCancelled(True)
            event.getPlayer().sendMessage("This chest is locked. You can't damage it.")

@hook.event("player_interact", "high")
def onPlayerIntreact(event): # Stops a user from opening a locked chest.
    block = event.getClickedBlock()
    player = Player(event.getPlayer())
    if not type(block) is NoneType:
        if str(block.type) == "CHEST":
            chest = Chest(block)
            if chest.isLocked():
                if not chest.isOwner(player):
                    if player.b.hasPermission("chestlocker.seeowner"):
                        player.msg("This chest is locked. You can't open it. It belongs to %s." % chest.chest['player'])
                    else:
                        player.msg("This chest is locked. You can't open it.")
                    event.setCancelled(True)
                else:
                    player.msg("You just opened a locked chest.")
            elif debug:
                player.msg("Debug: Chest is not locked")

@hook.event("entity_explode", "high")
def onExplode(event):
    for block in event.blockList():
        if type(block) != "NoneType":
            if str(block.type) == "CHEST":
                chest = Chest(block)
                if chest.isLocked():
                    event.setCancelled(True)
