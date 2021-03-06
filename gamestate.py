'''
This file stores the gamestate class that is used to keep track of
the current state of the dcss game 
'''

import actions
import logging
import re
import time
import string
import random
from enum import Enum


class ItemProperty(Enum):
    """
    See crawl wiki for lists of these:
    weapons: http://crawl.chaosforge.org/Brand
    armour: http://crawl.chaosforge.org/Ego
    """
    NO_PROPERTY = 0

    # Melee Weapon Brands
    Antimagic_Brand = 1
    Chaos_Brand = 2
    Disruption_Brand = 3
    Distortion_Brand = 4
    Dragon_slaying_Brand = 5
    Draining_Brand = 6
    Electrocution_Brand = 7
    Flaming_Brand = 8
    Freezing_Brand = 9
    Holywrath_Brand = 10
    Pain_Brand = 11
    Necromancy_Brand = 12
    Protection_Brand = 13
    Reaping_Brand = 14
    Speed_Brand = 15
    Vampiricism_Brand = 16
    Venom_Brand = 17
    Vorpal_Brand = 18

    # Thrown weapon brands
    Dispersal_Brand = 19
    Exploding_Brand = 20
    Penetration_Brand = 21
    Poisoned_Brand = 22
    Returning_Brand = 23
    Silver_Brand = 24
    Steel_Brand = 25

    # Needles
    Confusion_Brand = 26
    Curare_Brand = 27
    Frenzy_Brand = 28
    Paralysis_Brand = 29
    Sleeping_Brand = 30

    # Armour Properties (Egos)
    Resistance_Ego = 31
    Fire_Resistance_Ego = 32
    Cold_Resistance_Ego = 33
    Poison_Resistance_Ego = 34
    Positive_Energy_Ego = 35
    Protection_Ego = 36
    Invisibility_Ego = 37
    Magic_Resistance_Ego = 38
    Strength_Ego = 39
    Dexterity_Ego = 40
    Intelligence_Ego = 41
    Running_Ego = 42
    Flight_Ego = 43
    Stealth_Ego = 44
    See_Invisible_Ego = 45
    Archmagi_Ego = 46
    Ponderousness_Ego = 47
    Reflection_Ego = 48
    Spirit_Shield_Ego = 49
    Archery_Ego = 50


class CellRawStrDatum(Enum):
    """ These are the types of data that may appear in a raw str description of a cell from the server. """
    x = 0
    f = 1
    y = 2
    g = 3
    t = 4
    mf = 5
    col = 6


class Cell:
    '''
    Stores a cell of the map, not sure what all the information means yet
    '''

    def __init__(self, vals):
        '''
        Vals is a dictionary containing attributes, key must be a CellRawStrDatum
        '''

        self.raw = vals
        self.x = None
        self.f = None
        self.y = None
        self.g = None
        self.t = None
        self.mf = None
        self.col = None

        self.has_wall = False
        self.has_player = False
        self.has_stairs_down = False
        self.has_stairs_up = False
        self.has_closed_door = False
        self.has_open_door = False
        self.has_statue = False
        self.has_player_visited = False
        self.has_lava = False
        self.has_plant = False
        self.has_tree = False
        self.set_vals(vals)

    def set_vals(self, vals):
        if 'x' in vals.keys():
            self.x = vals['x']
        if 'f' in vals.keys():
            self.f = vals['f']
        if 'y' in vals.keys():
            self.y = vals['y']
        if 'g' in vals.keys():
            self.g = vals['g']

            if self.g == '#':
                self.has_wall = True

            if self.g == '>':
                self.has_stairs_down = True

            if self.g == '<':
                self.has_stairs_up = True

            if self.g == '@':
                self.has_player = True
                self.has_player_visited = True
            else:
                self.has_player = False

            if self.g == '+':
                self.has_closed_door = True
                self.has_closed_door = False

            if self.g == '\'':
                self.has_closed_door = False
                self.has_open_door = True

            if self.g == '8':
                self.has_statue = True

            if self.g == '≈' or self.g == '§':
                self.has_lava = True

            if self.g == 'P':
                self.has_plant = True

            if self.g == '☘':
                self.has_tree = True

        if 't' in vals.keys():
            self.t = vals['t']
        if 'mf' in vals.keys():
            self.mf = vals['mf']
        if 'col' in vals.keys():
            self.col = vals['col']

        self.raw = vals

    def get_pddl_name(self):
        return "cellx{}y{}".format(self.x, self.y)

    def get_cell_vector(self):
        """Do something similar to get_item_vector"""

        # cell vector should contain:
        # corpse? 0 or 1
        # monster? (can only be one monster on a tile) - monster vector with
            # monster vector
            # current health? (may be in the form of weak, almost dead, bloodied, etc)
            # maximum health?
            # monster name
            # is unique?
        # items?
        # special tile features (like water, lava, wall, door, etc)

    def get_pddl_facts(self):
        pddl_facts = []
        if self.has_wall:
            pddl_facts.append('(wall {})'.format(self.get_pddl_name()))
        if self.has_closed_door:
            pddl_facts.append('(closeddoor {})'.format(self.get_pddl_name()))
        if self.has_player:
            pddl_facts.append('(playerat {})'.format(self.get_pddl_name()))
        if self.has_statue:
            pddl_facts.append('(statue {})'.format(self.get_pddl_name()))
        if self.has_lava:
            pddl_facts.append('(lava {})'.format(self.get_pddl_name()))
        if self.has_plant:
            pddl_facts.append('(plant {})'.format(self.get_pddl_name()))
        if self.has_tree:
            pddl_facts.append('(tree {})'.format(self.get_pddl_name()))
        return pddl_facts

    def __str__(self):
        if self.g and len(self.g) >= 1:
            return self.g
        else:
            return " "


class CellMap:
    """
    Data structure that maintains the set of all cells currently seen in the game.
    """

    def __init__(self):
        self.min_x = None
        self.min_y = None
        self.max_x = None
        self.max_y = None
        self.num_cells = 0
        self.x_y_to_cells = {}  # key is an (x,y) tuple, val is the cell at that spot
        self.agent_x = None
        self.agent_y = None
        # unknown_vals = {k:None for k in CellRawStrDatum} # test this
        # self.unknown_cell = Cell(

    def add_or_update_cell(self, x, y, vals):
        #print("vals={}".format(str(vals)))

        if 'x' not in vals.keys():
            vals['x'] = x
        elif x != vals['x']:
            print("WARNING potential issue with coordinates, x={} and vals[x]={}".format(x, vals['x']))
        if 'y' not in vals.keys():
            vals['y'] = x
        elif y != vals['y']:
            print("WARNING potential with coordinates, y={} and vals[y]={}".format(y, vals['y']))

        if (x, y) in self.x_y_to_cells.keys():
            #print("updating existing cell x={},y={}".format(x,y))
            #print("previous vals={}, new vals={}".format(self.x_y_to_cells[(x, y)].raw, vals))
            self.x_y_to_cells[(x, y)].set_vals(vals=vals)
        else:
            #print("adding new cell x={},y={} with vals={}".format(x, y, vals))
            self.x_y_to_cells[(x, y)] = Cell(vals=vals)
            if self.min_x is None or x < self.min_x:
                self.min_x = x
            if self.max_x is None or x > self.max_x:
                self.max_x = x
            if self.min_y is None or y < self.min_y:
                self.min_y = y
            if self.max_y is None or y > self.max_y:
                self.max_y = y

        if 'g' in vals.keys() and '@' in vals['g']:
            self.agent_x = x
            self.agent_y = y

    def draw_cell_map(self):

        s = "agent=({},{})\nminx={},maxx={},miny={},maxy={}\n".format(self.agent_x, self.agent_y,
                                                              self.min_x, self.max_x, self.min_y, self.max_y)
        non_empty_cells = []
        for curr_y in range(self.min_y, self.max_y + 1):
            for curr_x in range(self.min_x, self.max_x + 1):
                if (curr_x, curr_y) in self.x_y_to_cells.keys():
                    cell = self.x_y_to_cells[(curr_x, curr_y)]
                    s += str(cell)
                    if cell.g != "." and cell.g != "#" and cell.g is not None:
                        non_empty_cells.append(cell)
                else:
                    s += " "
            s += '\n'

        #print("non-empty cells are:")
        #for c in non_empty_cells:
        #    print("X={},Y={}, Cell is: {}".format(c.x, c.y, c.g))

        return s

    def print_radius_around_agent(self, r=8):
        x_min = self.agent_x - r
        x_max = self.agent_x + r
        y_min = self.agent_y - r
        y_max = self.agent_y - r
        s = ""
        for curr_y in range(y_min, y_max + 1):
            for curr_x in range(x_min, x_max + 1):
                if (curr_x, curr_y) in self.x_y_to_cells.keys():
                    s += str(self.x_y_to_cells[(curr_x, curr_y)])
                else:
                    s += " "
            s += '\n'
        return s

    def get_cell_map_pddl(self, goals):

        object_strs = []
        fact_strs = []
        for curr_y in range(self.min_y, self.max_y + 1):
            for curr_x in range(self.min_x, self.max_x + 1):
                if (curr_x, curr_y) in self.x_y_to_cells.keys():
                    cell = self.x_y_to_cells[(curr_x, curr_y)]
                    object_strs.append(cell.get_pddl_name())

                    for f in cell.get_pddl_facts():
                        fact_strs.append(f)

                    #print('cellxy = {}, cellname is {}'.format(str((curr_x, curr_y)), cell.get_pddl_name()))
                    northcellxy = (cell.x, cell.y - 1)
                    #print("northcellxy = {}".format(northcellxy))
                    if northcellxy in self.x_y_to_cells.keys():
                        northcell = self.x_y_to_cells[northcellxy]
                        #print("northcell = {}".format(northcell.get_pddl_name()))
                        fact_strs.append("(northof {} {})".format(cell.get_pddl_name(), northcell.get_pddl_name()))

                    southcellxy = (cell.x, cell.y + 1)
                    if southcellxy in self.x_y_to_cells.keys():
                        southcell = self.x_y_to_cells[southcellxy]
                        fact_strs.append("(southof {} {})".format(cell.get_pddl_name(), southcell.get_pddl_name()))

                    westcellxy = (cell.x-1, cell.y)
                    if westcellxy in self.x_y_to_cells.keys():
                        westcell = self.x_y_to_cells[westcellxy]
                        fact_strs.append("(westof {} {})".format(cell.get_pddl_name(), westcell.get_pddl_name()))

                    eastcellxy = (cell.x + 1, cell.y)
                    if eastcellxy in self.x_y_to_cells.keys():
                        eastcell = self.x_y_to_cells[eastcellxy]
                        fact_strs.append("(eastof {} {})".format(cell.get_pddl_name(), eastcell.get_pddl_name()))

                    northeastcellxy = (cell.x + 1, cell.y - 1)
                    if northeastcellxy in self.x_y_to_cells.keys():
                        northeastcell = self.x_y_to_cells[northeastcellxy]
                        fact_strs.append("(northeastof {} {})".format(cell.get_pddl_name(), northeastcell.get_pddl_name()))

                    northwestcellxy = (cell.x - 1, cell.y - 1)
                    if northwestcellxy in self.x_y_to_cells.keys():
                        northwestcell = self.x_y_to_cells[northwestcellxy]
                        fact_strs.append(
                            "(northwestof {} {})".format(cell.get_pddl_name(), northwestcell.get_pddl_name()))

                    southeastcellxy = (cell.x + 1, cell.y + 1)
                    if southeastcellxy in self.x_y_to_cells.keys():
                        southeastcell = self.x_y_to_cells[southeastcellxy]
                        fact_strs.append(
                            "(southeastof {} {})".format(cell.get_pddl_name(), southeastcell.get_pddl_name()))

                    southwestcellxy = (cell.x - 1, cell.y + 1)
                    if southwestcellxy in self.x_y_to_cells.keys():
                        southwestcell = self.x_y_to_cells[southwestcellxy]
                        fact_strs.append(
                            "(southwestof {} {})".format(cell.get_pddl_name(), southwestcell.get_pddl_name()))

        object_strs = list(set(object_strs))
        fact_strs = list(set(fact_strs))

        pddl_str = "(define (problem dcss-test-prob)\n(:domain dcss)\n(:objects \n"

        for obj in object_strs:
            pddl_str+= "  {}\n".format(obj)
        pddl_str += ")\n"

        pddl_str += "(:init \n"
        for fact in fact_strs:
            pddl_str+= "  {}\n".format(fact)
        pddl_str += ")\n"

        pddl_str += "(:goal \n  (and \n"
        for goal in goals:
            pddl_str += "    {}\n".format(goal)
        pddl_str += ")\n"
        pddl_str += ")\n\n)"

        return pddl_str

    def get_xy_to_cells_dict(self):
        return self.x_y_to_cells


class InventoryItem:
    ITEM_VECTOR_LENGTH = 5

    def __init__(self, id_num, name, quantity, base_type=None):
        self.id_num = int(id_num)
        self.name = name
        self.quantity = quantity
        self.base_type = base_type
        self.item_bonus = 0
        self.properties = []

        if self.name:
            if '+' in self.name or '-' in self.name:
                m = re.search('[+-][1-9][1-9]?', self.name)
                if m:
                    self.item_bonus = int(m.group(0))
                else:
                    self.item_bonus = 0
        else:
            print(
                "\n\nself.name is None, not sure why...args to InventoryItem were id_num={}, name={}, quantity={}, base_type={}\n\n".format(
                    id_num, name, quantity, base_type))
            exit(1)

        # TODO - figure out how to know if item is equipped
        self.equipped = False

    def set_base_type(self, base_type):
        self.base_type = base_type

    def get_base_type(self):
        return self.base_type

    def set_name(self, name):
        self.name = name

    def get_name(self):
        return self.name

    def set_quantity(self, quantity):
        self.quantity = quantity

    def get_quantity(self):
        return self.quantity

    def set_num_id(self, id_num):
        self.id_num = int(id_num)

    def get_num_id(self):
        return self.id_num

    def get_letter(self):
        return string.ascii_letters[self.id_num]

    def get_item_bonus(self):
        return self.item_bonus

    def is_item_equipped(self):
        return self.equipped

    def get_item_type(self):
        """
        Since 0 is a valid value, increase all by 1, so 0 means an empty value
        """
        return 1 + self.base_type

    def get_property_i(self, i):
        if i < len(self.properties):
            return self.properties[i]
        else:
            return ItemProperty.NO_PROPERTY

    def get_item_vector(self):
        """
        * Indicates that item vector value may be repeated, if more than one property.

        Index  Information Contained
        -----  ---------------------
          0    Item Type (Armour, Weapon, etc)
          1    Item Count
          2    Item Bonus ("+x" value)
          3    Item Equipped
          4    Property* (Fire resist, stealth, venom, etc)
        """
        item_vector = []
        item_vector.append(self.get_item_type())
        item_vector.append(self.get_quantity())
        item_vector.append(self.get_item_bonus())
        item_vector.append(self.is_item_equipped())
        item_vector.append(self.get_property_i(0))

        assert len(item_vector) == InventoryItem.ITEM_VECTOR_LENGTH
        # Note: If this assert fails, update
        # InventoryItem.ITEM_VECTOR_LENGTH to be the correct value

        return item_vector

    @staticmethod
    def get_empty_item_vector():
        item_vector = [0 for i in range(InventoryItem.ITEM_VECTOR_LENGTH)]
        return item_vector

    def __eq__(self, other):
        return self.name == other.name

    def __str__(self):
        return "{}({}) - {} (#={}, base_type={})".format(self.get_letter(), self.id_num, self.get_name(),
                                                             self.get_quantity(), self.get_base_type())

class TileFeatures:
    '''
    Contains feature data used per tile

    Returns a factored state representation of the tiles around the player:
        Example w/ radius of 1
        - 9 tiles including the player's current position and all adjacent tiles in every cardinal direction
        - each tile is represented as a factored state:
          <objType,monsterLetter,hasCorpse,hereBefore>
             * objType = 0 is empty, 1 is wall, 2 is monster
             * monsterLetter = 0-25 representing the alpha index of the first letter of mon name (0=a, etc)
             * hasCorpse = 0 if no edible corpse, 1 if edible corpse
             * hereBefore = 0 if first time player on this tile, 1 if player has already been here
    '''

    absolute_x = None
    absolute_y = None
    has_monster = 0
    last_visit = None  # None if never visited, 0 if currently here, otherwise >1 representing
    # number of actions executed since last visit


class GameState:
    ID = 0

    def __init__(self):
        # state is just a dictionary of key value pairs
        self.state = {}

        # only state information we care about
        self.state_keys = ['hp', 'hp_max', 'depth', 'light', 'god', 'mp', 'species', 'dex', 'inv', 'cells', 'species']

        self.letter_to_number_lookup = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i']

        # when the agent starts, it is in the center of its mental map
        # as it moves N,S,E,W, the coordinates of its mental map will shift
        self.agent_x = 0
        self.agent_y = 0
        self.agent_z = 0  # which floor of the dungeon the agent is on

        self.map_obj_player_x = None  # this is the x of the map_obj where the player is
        self.map_obj_player_y = None  # this is the y of the map_obj where the player is

        self.map_obj = []
        self.map_dim = 24
        self.map_middle = 12
        self.cellmap = CellMap()

        self.inventory_by_id = {}

        self.last_recorded_movement = ''

        self.asp_str = ''  # facts that don't change when an action is executed
        self.asp_comment_str = ''  # comments associated with asp
        self.player_cell = None
        self.training_asp_str = ''  # facts that do change
        self.all_asp_cells = None  # number of cell objects

        self.messages = {}  # key is turn, value is list of messages received on this turn in order,
        # where first is oldest message

        # initialize values of state variables
        for k in self.state_keys:
            self.state[k] = None

        self.died = False  # becomes true if agent has died

        self.more_prompt = False  # becomes true when there is more messages before the agent can act
        #  and therefore must press enter to receive for messages

        self.too_terrified_to_move = False  # idk what to do here, but agent can't move

        self.cannot_move = False  # agent can't move for some reason, no use trying move actions

        self.just_gained_level = False

        self.id = GameState.ID
        GameState.ID += 1

    def update(self, msg_from_server):
        try:
            # print(str(self.state))
            logging.info(str(msg_from_server))
            self._process_raw_state(msg_from_server)
            # self.draw_map()
            # self.compute_asp_str()
            # print(self.training_asp_str)
            # print(self.background_asp_str)
        except Exception as e:
            raise Exception("Something went wrong" + e)

    def record_movement(self, dir):
        self.last_recorded_movement = dir
        print('last recorded movement is ' + str(self.last_recorded_movement))
        if dir in actions.key_actions.keys():
            if dir is 'move_N':
                self.shift_agent_y(-1)
            elif dir is 'move_S':
                self.shift_agent_y(1)
            elif dir is 'move_E':
                self.shift_agent_x(1)
            elif dir is 'move_W':
                self.shift_agent_x(-1)
            else:
                pass  # do nothing if the agent didn't move
        pass  # do nothing if the agent didn't move

    def shift_agent_x(self, change):
        '''
        Performs an addition
        '''
        self.agent_x += change

    def shift_agent_y(self, change):
        '''
        Performs an addition
        '''
        self.agent_y += change

    def get_cell_map(self):
        return self.cellmap

    def _process_raw_state(self, s, last_key=''):
        # print("processing {}\n\n".format(s))
        if isinstance(s, list):
            for i in s:
                self._process_raw_state(i)

        elif isinstance(s, dict):
            for k in s.keys():
                if k == 'cells':
                    self.get_cell_objs_from_raw_data(s[k])
                    # self.update_map_obj(cells_x_y_g_data_only)
                    # self.update_map_obj()
                last_key = k

                if k == 'messages':
                    self.process_messages(s[k])
                if k == 'inv':
                    self.process_inv(s[k])

                if k in self.state_keys:
                    self.state[k] = s[k]
                    # print("Just stored {} with data {}".format(k,s[k]))
                elif isinstance(s[k], list):
                    for i in s[k]:
                        self._process_raw_state(i)
                elif isinstance(s[k], dict):
                    self._process_raw_state(s[k])
                else:
                    pass
        else:
            pass

    def _process_items_agent_location(self, message):
        items = message.split(';')
        print("Found {} items, they are:".format(len(items)))
        for i in items:
            print("   {}".format(i))

    def process_messages(self, data):
        # begin: this is just for html stripping
        from html.parser import HTMLParser
        class MLStripper(HTMLParser):
            def __init__(self):
                self.reset()
                self.strict = False
                self.convert_charrefs = True
                self.fed = []

            def handle_data(self, d):
                self.fed.append(d)

            def get_data(self):
                return ''.join(self.fed)

        def strip_tags(html):
            s = MLStripper()
            s.feed(html)
            return s.get_data()

        # end: html stripping code

        last_message_is_items_here = False
        for m in data:
            turn = m['turn']
            message_only = strip_tags(m['text'])
            if turn in self.messages.keys():
                self.messages[turn].append(message_only)
            else:
                self.messages[turn] = [message_only]

            if 'You die...' in message_only:
                self.died = True

            if len(self.messages[turn]) >= 8:
                self.more_prompt = True

            if 'too terrified to move' in message_only:
                self.too_terrified_to_move = True

            if 'You cannot move' in message_only:
                self.cannot_move = True

            if 'You have reached level' in message_only:
                self.just_gained_level = True

            if last_message_is_items_here:
                self._process_items_agent_location(message_only)
                last_message_is_items_here = False

            if 'Things that are here' in message_only:
                last_message_is_items_here = True

            if 'Unknown command.' in message_only:
                print("Error with last command - game did not recognize it... sleeping for 30 seconds")
                time.sleep(30)

            print("Just added message for turn {}: {}".format(turn, message_only))

    def get_pddl_current_state(self, goals):
        return self.cellmap.get_cell_map_pddl(goals)

    def write_pddl_current_state_to_file(self, filename, goals):
        """Filename is assumed to be a relevant filename from the folder that the main script is running"""

        with open(filename.format(), 'w') as f:
            f.write(self.get_pddl_current_state(goals))

        return True

    def has_agent_died(self):
        return self.died

    def is_agent_too_terrified(self, reset=True):
        agent_terrified = self.too_terrified_to_move
        if reset:
            self.too_terrified_to_move = False
        return agent_terrified

    def agent_cannot_move(self, reset=True):
        cannot_move = self.cannot_move
        if reset:
            self.cannot_move = False
        return cannot_move

    def agent_just_leveled_up(self, reset=True):
        leveled_up = self.just_gained_level
        if reset:
            self.just_gained_level = False
        return leveled_up

    def game_has_more_messages(self, reset=False):
        more_prompt = self.more_prompt
        if reset:
            self.more_prompt = False
        return more_prompt

    def process_inv(self, data):
        print("Data is {}".format(data))
        for inv_id in data.keys():
            name = None
            quantity = None
            base_type = None
            if 'name' in data[inv_id].keys():
                name = data[inv_id]['name']
            if 'quantity' in data[inv_id].keys():
                quantity = int(data[inv_id]['quantity'])
            if 'base_type' in data[inv_id].keys():
                base_type = data[inv_id]['base_type']
            if inv_id not in self.inventory_by_id.keys():
                # new item
                inv_item = InventoryItem(inv_id, name, quantity, base_type)
                self.inventory_by_id[inv_id] = inv_item
                print("***** Adding new item {}".format(inv_item))
            else:
                # existing item
                inv_item = self.inventory_by_id[inv_id]
                print("***** Updating item {}".format(inv_item))
                prev_quantity = inv_item.get_quantity()
                if quantity is not None and quantity <= prev_quantity:
                    if quantity == 0:
                        print("  **** Deleting item {} because quantity = 0".format(inv_item))
                        del self.inventory_by_id[inv_id]
                    else:
                        print("  **** Reducing item {} quantity from {} to {}".format(inv_item, prev_quantity, quantity))
                        self.inventory_by_id[inv_id].set_quantity(quantity)

    def get_cell_objs_from_raw_data(self, cells):
        only_xyg_cell_data = []
        curr_x = None
        curr_y = None
        g_var = None
        num_at_signs = 0
        if cells:
            # Note: in the first iteration of this loop, x and y will exist in cell_dict.keys()
            for cell_dict in cells:
                # either x and y appear to mark the start of a new row, or ...
                if 'x' in cell_dict.keys() and 'y' in cell_dict.keys():
                    curr_x = cell_dict['x']
                    curr_y = cell_dict['y']
                else:  # ... just increment x, keeping y the same
                    curr_x += 1

                #print("x={},y={}".format(curr_x, curr_y))

                vals = {}

                # store any other datums we have access to
                for datum_key in CellRawStrDatum:
                    if datum_key.name in cell_dict.keys():
                        #input("datum_key {} is in cell_dict {} with value {}".format(datum_key.name, cell_dict, cell_dict[datum_key.name]))
                        vals[datum_key.name] = cell_dict[datum_key.name]
                    else:
                        pass
                        # input("datum_key {} is NOT in cell_dict {}".format(datum_key.name, cell_dict))
                if 'x' not in vals.keys():
                    vals['x'] = curr_x
                if 'y' not in vals.keys():
                    vals['y'] = curr_y

                self.cellmap.add_or_update_cell(curr_x, curr_y, vals=vals)

    def update_map_obj(self):
        '''
        If we already have a map data, and we have new map data from the player moving,
        shift the map and update the cells

        :param cell_data_raw:
        :param player_move_dir:
        '''

        # print("cells data is {}".format(cell_data_raw))
        # todo - left off here, figure out how to update the global cells as the player moves
        # todo - do we need to shift cells? or only change the player's current x and y? The latter
        # todo - would be ideal.
        at_sign_count = 0  # we should only see the @ in one location

        # If map object isn't created yet, then initialize
        if len(self.map_obj) == 0:
            for i in range(self.map_dim):
                row = [' '] * self.map_dim
                self.map_obj.append(row)

        if not cell_data_raw:
            # We don't always get cell data, if so, return
            return

        if cell_data_raw:
            print("Raw cells data:")
            prev_x = None
            prev_y = None
            for cell_raw_str in cell_data_raw:
                # x, y, g = cell_raw_str['x']
                print("  {}".format(cell_raw_str))

        for xyg_cell in cell_data_raw:
            x = int(xyg_cell[0])
            y = int(xyg_cell[1])
            g = xyg_cell[2]

            map_obj_x = self.map_middle + x
            map_obj_y = self.map_middle + y

            if '@' == g:
                # print("player x,y is " + str(x) + ',' + str(y) + " from cell data")
                # print("player x,y in gamestate is " + str(map_obj_x) + ',' + str(map_obj_y) + " from cell data")
                self.map_obj_player_x = map_obj_x
                self.map_obj_player_y = map_obj_y
                at_sign_count += 1
                if at_sign_count > 1:
                    print("Error, multiple @ signs - let's debug!")
                    time.sleep(1000)

            # boundary conditions
            if map_obj_y < len(self.map_obj) and \
                    map_obj_x < len(self.map_obj[map_obj_y]) and \
                    map_obj_x > 0 and \
                    map_obj_y > 0:
                self.map_obj[map_obj_y][map_obj_x] = g

    def print_map_obj(self):
        while self.lock:
            # wait
            time.sleep(0.001)

        self.lock = True
        try:
            for r in self.map_obj:
                print(str(r))
            self.lock = False
        except:
            raise Exception("Oh man something happened")
        finally:
            self.lock = False

    def get_player_xy(self):
        return (self.map_obj_player_x, self.map_obj_player_y)

    def get_asp_str(self):
        return self.asp_str

    def get_asp_comment_str(self):
        return self.asp_comment_str

    def get_training_asp_str(self):
        return self.training_asp_str

    def get_player_cell(self):
        return self.player_cell

    def get_tiles_around_player_radius(self, radius=1):
        '''
        A radius of 0 is only the players tile
        A radius of 1 would be 9 tiles, including
            - players tile
            - all tiles 1 away (including diagonal) of the player's tile
        A radius of 2 would be 16+8+1 = 25 tiles (all tiles <= distance of 2 from player)
        etc...

        Returns a factored state representation of the tiles around the player:
        Example w/ radius of 1
        - 9 tiles including the player's current position and all adjacent tiles in every cardinal direction
        - tiles are ordered in a clockwise orientation, starting with N, then NE, then E, etc
        - inner layers come before outer layers
        - each tile is represented as a factored state:
          <objType,monsterLetter,hasCorpse,hereBefore>
             * objType = 0 is empty, 1 is wall, 2 is monster
             * monsterLetter = 27 if noMonster, 0-26 representing the alpha index of the first letter of mon name
             * hasCorpse = 0 if no edible corpse, 1 if edible corpse
             * hereBefore = 0 if first time player on this tile, 1 if player has already been here


        :param radius: Int
        :return: a factored state representation of the tiles around the player
        '''

        tiles = []
        curr_radius = 0

        # agent's tile
        tiles.append(self.map_obj[self.map_obj_player_y][self.map_obj_player_x])
        # N tile
        tiles.append(self.map_obj[self.map_obj_player_y - 1][self.map_obj_player_x])
        # NE tile
        tiles.append(self.map_obj[self.map_obj_player_y - 1][self.map_obj_player_x + 1])
        # E tile
        tiles.append(self.map_obj[self.map_obj_player_y][self.map_obj_player_x + 1])
        # SE tile
        tiles.append(self.map_obj[self.map_obj_player_y + 1][self.map_obj_player_x + 1])
        # S tile
        tiles.append(self.map_obj[self.map_obj_player_y + 1][self.map_obj_player_x])
        # SW tile
        tiles.append(self.map_obj[self.map_obj_player_y + 1][self.map_obj_player_x - 1])
        # W tile
        tiles.append(self.map_obj[self.map_obj_player_y][self.map_obj_player_x - 1])
        # NW tile
        tiles.append(self.map_obj[self.map_obj_player_y - 1][self.map_obj_player_x - 1])

        return tiles

    def draw_map(self):
        # print("in draw map!")
        s = ''
        top_row_indexes = None
        for row in self.map_obj:
            row_s = ''
            if top_row_indexes is None:
                # not sure what I was doing here?
                pass
            for spot in row:
                if len(spot) != 0:
                    row_s += (str(spot))
                else:
                    row_s += ' '
            # remove any rows that are all whitespace
            if len(row_s.strip()) > 0:
                s += row_s + '\n'

        print(s)

    def draw_cell_map(self):
        print(self.cellmap.draw_cell_map())

    def print_inventory(self):
        print("   Inventory:")
        for inv_item in sorted(self.inventory_by_id.values(), key=lambda i: i.get_num_id()):
            print("     {} - {} (#={}, base_type={})".format(inv_item.get_letter(), inv_item.get_name(),
                                                             inv_item.get_quantity(), inv_item.get_base_type()))
            print("     Vector: {}".format(inv_item.get_item_vector()))

    def get_inventory_vector(self):
        pass

    def _pretty_print(self, curr_state, offset=1, last_key=''):
        if not isinstance(curr_state, dict):
            print(' ' * offset + str(curr_state))
        else:
            for key in curr_state.keys():
                last_key = key
                if isinstance(curr_state[key], dict):
                    print(' ' * offset + str(key) + '= {')
                    self._pretty_print(curr_state[key], offset + 2, last_key)
                    print(' ' * offset + '}')
                elif isinstance(curr_state[key], list):
                    if last_key == 'cells':
                        # don't recur
                        self.print_x_y_g_cell_data(curr_state[key])
                        # for i in curr_state[key]:
                        #    print('  '*offset+str(i))
                        # pass
                    else:
                        print(' ' * offset + str(key) + '= [')
                        for i in curr_state[key]:
                            self._pretty_print(i, offset + 2, last_key)
                        print(' ' * offset + "--")
                    print(' ' * offset + ']')

                else:
                    print(' ' * offset + str(key) + "=" + str(curr_state[key]))

    def printstate(self):
        # print("self.state="+str(self.state))
        # print('-'*20+" GameState "+'-'*20)
        # self._pretty_print(self.state)
        pass

    def get_map_obj(self):
        return self.map_obj

    def convert_cells_to_map_obj(self, cells_str):
        '''
        cells is the data of the map and nearby monsters and enemies received from the server
        '''
        map_dim = 200
        map_middle = 100
        for i in range(map_dim):
            row = [' '] * map_dim
            self.map_obj.append(row)

        curr_x = -1
        for cell in cells_str:
            # create Cell object
            new_cell = Cell(cell)

            # put into right location into map
            if new_cell.x and new_cell.y and new_cell.g:
                curr_x = new_cell.x
                self.map_obj[new_cell.y + map_middle][new_cell.x + map_middle] = new_cell.g

                # map_obj[abs(new_cell.x)][abs(new_cell.y)] = new_cell.g
            # elif new_cell.y and new_cell.g and curr_x >= 0:
            #    map_obj[new_cell.y+map_middle][curr_x] = new_cell.g
            # map_obj[curr_x][abs(new_cell.y)] = new_cell.g

        def print_map_obj(self):
            for row in self.map_obj:
                for spot in row:
                    print(str(spot), end='')
                print('')


class FactoredState():
    '''
    Represents a factored state for use for q-learning.

    State Information:
    - 9 tiles including the player's current position and all adjacent tiles in every cardinal direction
        - each tile is represented as a factored state:
          <objType,monsterLetter,hasCorpse,hereBefore>
             * objType = 0 is empty, 1 is wall, 2 is monster
             * monsterLetter = -1 if noMonster, 0-26 representing the alpha index of the first letter of mon name
             * hasCorpse = 0 if no edible corpse, 1 if edible corpse
             * hereBefore = 0 if first time player on this tile, 1 if player has already been here
    - player's health, enums of [none,verylow,low,half,high,veryhigh,full]
    - player's hunger, enums of [fainting,starving,very hungry, hungry, not hungry, full, very full, engorged]

    '''

    tiles = []
    health = None
    hunger = None

    def __init__(self, gs):
        map_obj = gs.get_map_obj()


if __name__ == '__main__':
    example_json_state_string_1 = {'msgs': [{'msg': 'map', 'clear': True, 'cells': [
        {'f': 9, 'col': 1, 'g': '#', 't': {'bg': 1847}, 'x': -6, 'mf': 2, 'y': -1},
        {'f': 9, 'g': '#', 'mf': 2, 'col': 1, 't': {'bg': 1848}},
        {'f': 9, 'g': '#', 'mf': 2, 'col': 1, 't': {'bg': 1846}},
        {'f': 9, 'g': '#', 'mf': 2, 'col': 1, 't': {'bg': 1847}},
        {'f': 9, 'g': '#', 'mf': 2, 'col': 1, 't': {'bg': 1846}},
        {'f': 9, 'g': '#', 'mf': 2, 'col': 1, 't': {'bg': 1846}},
        {'f': 9, 'g': '#', 'mf': 2, 'col': 1, 't': {'bg': 1847}},
        {'f': 9, 'g': '#', 'mf': 2, 'col': 1, 't': {'bg': 1847}},
        {'f': 9, 'g': '#', 'mf': 2, 'col': 1, 't': {'bg': 1848}},
        {'f': 9, 'g': '#', 'mf': 2, 'col': 1, 't': {'bg': 1846}},
        {'f': 9, 'g': '#', 'mf': 2, 'col': 1, 't': {'bg': 1848}},
        {'f': 9, 'col': 1, 'g': '#', 't': {'bg': 1847}, 'x': -6, 'mf': 2, 'y': 0},
        {'f': 33, 'g': '.', 'mf': 1, 'col': 7, 't': {'bg': 9, 'ov': [2202, 2204]}},
        {'f': 33, 'g': '$', 'mf': 6, 'col': 14,
         't': {'doll': None, 'ov': [2204], 'fg': 947, 'mcache': None, 'bg': 1048585, 'base': 0}},
        {'f': 33, 'g': '.', 'mf': 1, 'col': 7, 't': {'bg': 4, 'ov': [2204]}},
        {'f': 33, 'g': '.', 'mf': 1, 'col': 7, 't': {'bg': 2, 'ov': [2204]}}, {'f': 33, 'g': '0', 'mf': 6, 'col': 5,
                                                                               't': {'doll': None, 'ov': [2204],
                                                                                     'fg': 842, 'mcache': None, 'bg': 2,
                                                                                     'base': 0}},
        {'f': 33, 'g': '@', 'mf': 1, 'col': 87,
         't': {'mcache': None, 'doll': [[3302, 32], [3260, 32], [3372, 32], [3429, 32], [4028, 32], [3688, 32]],
               'bg': 7, 'ov': [2204], 'fg': 527407}},
        {'f': 33, 'g': '.', 'mf': 1, 'col': 7, 't': {'bg': 5, 'ov': [2204]}}, {'f': 33, 'g': '$', 'mf': 6, 'col': 14,
                                                                               't': {'doll': None, 'ov': [2204],
                                                                                     'fg': 947, 'mcache': None,
                                                                                     'bg': 1048580, 'base': 0}},
        {'f': 33, 'g': '.', 'mf': 1, 'col': 7, 't': {'bg': 6, 'ov': [2204, 2206]}},
        {'f': 9, 'g': '#', 'mf': 2, 'col': 1, 't': {'bg': 1845}},
        {'f': 9, 'col': 1, 'g': '#', 't': {'bg': 1848}, 'x': -6, 'mf': 2, 'y': 1},
        {'f': 33, 'g': '.', 'mf': 1, 'col': 7, 't': {'bg': 3, 'ov': [2202]}},
        {'f': 33, 'g': '.', 'mf': 1, 'col': 7, 't': {'bg': 4}}, {'f': 33, 'g': '.', 'mf': 1, 'col': 7, 't': {'bg': 5}},
        {'f': 33, 'g': '.', 'mf': 1, 'col': 7, 't': {'bg': 5}}, {'f': 33, 'g': '.', 'mf': 1, 'col': 7, 't': {'bg': 6}},
        {'f': 33, 'g': '.', 'mf': 1, 'col': 7, 't': {'bg': 4}}, {'f': 33, 'g': '.', 'mf': 1, 'col': 7, 't': {'bg': 3}},
        {'f': 33, 'g': '.', 'mf': 1, 'col': 7, 't': {'bg': 6}},
        {'f': 33, 'g': '.', 'mf': 1, 'col': 7, 't': {'bg': 4, 'ov': [2206]}},
        {'f': 9, 'g': '#', 'mf': 2, 'col': 1, 't': {'bg': 1848}},
        {'f': 9, 'col': 1, 'g': '#', 't': {'bg': 1846}, 'x': -6, 'mf': 2, 'y': 2},
        {'f': 33, 'g': '.', 'mf': 1, 'col': 7, 't': {'bg': 3, 'ov': [2202]}},
        {'f': 33, 'g': '.', 'mf': 1, 'col': 7, 't': {'bg': 6}}, {'f': 33, 'g': '.', 'mf': 1, 'col': 7, 't': {'bg': 3}},
        {'f': 33, 'g': '.', 'mf': 1, 'col': 7, 't': {'bg': 3}}, {'f': 33, 'g': '.', 'mf': 1, 'col': 7, 't': {'bg': 9}},
        {'f': 33, 'g': '.', 'mf': 1, 'col': 7, 't': {'bg': 5}}, {'f': 33, 'g': '.', 'mf': 1, 'col': 7, 't': {'bg': 2}},
        {'f': 33, 'g': '.', 'mf': 1, 'col': 7, 't': {'bg': 7}},
        {'f': 33, 'g': '.', 'mf': 1, 'col': 7, 't': {'bg': 3, 'ov': [2206]}},
        {'f': 9, 'g': '#', 'mf': 2, 'col': 1, 't': {'bg': 1847}},
        {'f': 9, 'col': 1, 'g': '#', 't': {'bg': 1846}, 'x': -6, 'mf': 2, 'y': 3},
        {'f': 33, 'g': '.', 'mf': 1, 'col': 7, 't': {'bg': 4, 'ov': [2202]}},
        {'f': 33, 'g': '.', 'mf': 1, 'col': 7, 't': {'bg': 7}}, {'f': 33, 'g': '.', 'mf': 1, 'col': 7, 't': {'bg': 5}},
        {'f': 33, 'g': '.', 'mf': 1, 'col': 7, 't': {'bg': 5}}, {'f': 33, 'g': '.', 'mf': 1, 'col': 7, 't': {'bg': 4}},
        {'f': 33, 'g': '.', 'mf': 1, 'col': 7, 't': {'bg': 6}}, {'f': 33, 'g': '.', 'mf': 1, 'col': 7, 't': {'bg': 6}},
        {'f': 33, 'g': '.', 'mf': 1, 'col': 7, 't': {'bg': 7}},
        {'f': 33, 'g': '.', 'mf': 1, 'col': 7, 't': {'bg': 2, 'ov': [2206]}},
        {'f': 9, 'g': '#', 'mf': 2, 'col': 1, 't': {'bg': 1847}},
        {'f': 9, 'col': 1, 'g': '#', 't': {'bg': 1845}, 'x': -6, 'mf': 2, 'y': 4},
        {'f': 33, 'g': '.', 'mf': 1, 'col': 7, 't': {'bg': 7, 'ov': [2202]}},
        {'f': 33, 'g': '.', 'mf': 1, 'col': 7, 't': {'bg': 7}}, {'f': 33, 'g': '.', 'mf': 1, 'col': 7, 't': {'bg': 3}},
        {'f': 33, 'g': '.', 'mf': 1, 'col': 7, 't': {'bg': 7}}, {'f': 33, 'g': '.', 'mf': 1, 'col': 7, 't': {'bg': 9}},
        {'f': 33, 'g': '.', 'mf': 1, 'col': 7, 't': {'bg': 4}}, {'f': 33, 'g': '.', 'mf': 1, 'col': 7, 't': {'bg': 7}},
        {'f': 33, 'g': '.', 'mf': 1, 'col': 7, 't': {'bg': 8}},
        {'f': 33, 'g': '.', 'mf': 1, 'col': 7, 't': {'bg': 8, 'ov': [2206]}},
        {'f': 9, 'g': '#', 'mf': 2, 'col': 1, 't': {'bg': 1845}},
        {'f': 9, 'col': 1, 'g': '#', 't': {'bg': 1845}, 'x': -6, 'mf': 2, 'y': 5},
        {'f': 33, 'g': '.', 'mf': 1, 'col': 7, 't': {'bg': 3, 'ov': [2202]}},
        {'f': 33, 'g': '.', 'mf': 1, 'col': 7, 't': {'bg': 5}}, {'f': 33, 'g': '.', 'mf': 1, 'col': 7, 't': {'bg': 3}},
        {'f': 33, 'g': '.', 'mf': 1, 'col': 7, 't': {'bg': 2}},
        {'f': 60, 'g': '<', 'mf': 12, 'col': 9, 't': {'bg': 2381, 'flv': {'f': 6, 's': 50}}},
        {'f': 33, 'g': '.', 'mf': 1, 'col': 7, 't': {'bg': 5}}, {'f': 33, 'g': '.', 'mf': 1, 'col': 7, 't': {'bg': 5}},
        {'f': 33, 'g': '.', 'mf': 1, 'col': 7, 't': {'bg': 2}},
        {'f': 33, 'g': '.', 'mf': 1, 'col': 7, 't': {'bg': 4, 'ov': [2206]}},
        {'f': 9, 'g': '#', 'mf': 2, 'col': 1, 't': {'bg': 1847}},
        {'f': 9, 'col': 1, 'g': '#', 't': {'bg': 1847}, 'x': -6, 'mf': 2, 'y': 6},
        {'f': 9, 'g': '#', 'mf': 2, 'col': 1, 't': {'bg': 1848}},
        {'f': 9, 'g': '#', 'mf': 2, 'col': 1, 't': {'bg': 1845}},
        {'f': 9, 'g': '#', 'mf': 2, 'col': 1, 't': {'bg': 1846}},
        {'f': 9, 'g': '#', 'mf': 2, 'col': 1, 't': {'bg': 1845}},
        {'f': 9, 'g': '#', 'mf': 2, 'col': 1, 't': {'bg': 1846}},
        {'f': 9, 'g': '#', 'mf': 2, 'col': 1, 't': {'bg': 1845}},
        {'f': 9, 'g': '#', 'mf': 2, 'col': 1, 't': {'bg': 1848}},
        {'f': 9, 'g': '#', 'mf': 2, 'col': 1, 't': {'bg': 1848}},
        {'f': 9, 'g': '#', 'mf': 2, 'col': 1, 't': {'bg': 1845}},
        {'f': 9, 'g': '#', 'mf': 2, 'col': 1, 't': {'bg': 1848}}], 'player_on_level': True, 'vgrdc': {'y': 0, 'x': 0}}]}
    example_json_state_string_2 = "{'msgs': [{'msg': 'input_mode', 'mode': 0}, {'msg': 'player', 'turn': 12, 'time': 120, 'pos': {'y': 1, 'x': -1}}, {'msg': 'map', 'cells': [{'col': 7, 'y': 0, 'g': '.', 't': {'mcache': None, 'doll': None, 'fg': 0}, 'x': 0}, {'col': 87, 'y': 1, 'g': '@', 't': {'mcache': None, 'doll': [[3302, 32], [3260, 32], [3372, 32], [3429, 32], [4028, 32], [3688, 32]], 'fg': 527407}, 'x': -1}], 'vgrdc': {'y': 1, 'x': -1}}, {'msg': 'input_mode', 'mode': 1}]}"

    gs1 = GameState()

    gs1.update(example_json_state_string_1)

'''
                        
    int:4
    species:Minotaur
    equip:{'0': 0, '15': -1, '8': -1, '1': -1, '12': -1, '9': -1, '11': -1, '18': -1, '17': -1, '4': -1, '3': -1, '7': -1, '16': -1, '14': -1, '10': -1, '6': 1, '2': -1, '5': -1, '13': -1}
    dex_max:9
    unarmed_attack:Nothing wielded
    penance:0
    form:0
    int_max:4
    poison_survival:16
    turn:1114
    str_max:21
    place:Dungeon
    name:midca
    dex:9
    ev:12
    hp_max:20
    real_hp_max:20
    mp_max:0
    unarmed_attack_colour:7
    piety_rank:1
    mp:0
    xl:1
    ac:2
    title:the Skirmisher
    hp:16
    
'''

'''
    def _process_raw_state3(self, dict_struct):
        if isinstance(dict_struct, list):
            new_li = []
            for li in dict_struct:
                new_li.append(self._process_raw_state(li))
            return new_li
        elif not isinstance(dict_struct, dict):
            return dict_struct
        else:
            curr_state = {}
            ignore_list = ['cell','html','content','skip','text']
            skip_bc_ignore = False
            for key in dict_struct.keys():
                for ignore in ignore_list:
                    if ignore in key:
                        skip_bc_ignore = True
                    
                    if skip_bc_ignore:
                        skip_bc_ignore = False
                        pass

                    # process if list
                    elif isinstance(dict_struct[key], list):
                        new_list = []
                        for li in dict_struct[key]:
                            new_list.append(self._process_raw_state(li))
                            
                            curr_state[key] = li
#                        else:
#                            curr_state[key] = dict_struct[key]

                    # process if dict
                    elif isinstance(dict_struct[key], dict):
                        curr_state[key] = self._process_raw_state(dict_struct[key])
                    else: 
                        curr_state[key] = dict_struct[key]

        return curr_state



'''
