import psutil, subprocess, random, ast, string, math, os, itertools, calendar, ipaddress, logging, json
from operator import itemgetter
from datetime import timedelta, time, datetime
from statistics import NormalDist
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import pytz

from collections import Counter

class BufferedRandomChoiceGenerator:
    def __init__(self, options, probabilities, buffer_size):
        self.options = options
        self.probabilities = probabilities
        self.buffer_size = buffer_size
        self.index = 0
        self.generate_new_buffer()

    def generate_new_buffer(self):
        self.buffer = np.random.choice(self.options, p = self.probabilities, size=self.buffer_size)
    
    def generate(self):
        while True:
            if self.index >= len(self.buffer):
                self.index = 0
                self.generate_new_buffer()
            choice = self.buffer[self.index]
            self.index += 1
            yield choice

class UtilsParams:
    def __init__(self, outlier_rate, outlier_cost, action_operations, priority_levels, debug, logger):
        
        self.outlier_rate = outlier_rate
        self.outlier_cost = outlier_cost
        self.action_operations = action_operations
        self.priority_levels = priority_levels
        self.debug = debug        
        self.logger = logger  
        
# Utils Class
class Utils:
    
    # Logs data
    def log_data(logger, message):
        
        if len(logger.handlers) > 0:
            logger.info(message)
      
    # Logs and debugs the data and processes undertaken
    def debug_and_log_data(debug, logger, message):
        
        if debug:
            print(message)
            
        if len(logger.handlers) > 0:
            logger.info(message)
    
    # Closes any excel file opened (prevents output wrinting fail)
    def close_excel():
    
        #print("Aqui")
        excel_found = False
        for proc in psutil.process_iter():
            if proc.name() == "EXCEL.EXE": 
                print("Excel instances found!")
                excel_found = True
                subprocess.call(["taskkill", "/f", "/im", "EXCEL.EXE"])            
        if not excel_found:
            print("Excel instances not found!")
            
    # Checks if the folder exists and has any file
    def is_folder_empty(folder_path):
        if not os.path.isdir(folder_path):
            raise ValueError(f"The path '{folder_path}' is not a valid directory.")

        # Check if the directory is empty
        return len(os.listdir(folder_path)) == 0
    
    # Gets most recent real dataset file
    def get_most_recent_file(folder_path):
        
        files = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
   
        if not files:
            raise ValueError(f"The folder '{folder_path}' is empty or contains no files.")

        # Find the file with the most recent modification time
        most_recent_file = max(files, key=os.path.getmtime)
        print("Most recent file:", type(most_recent_file))
        return most_recent_file
            
    # Encodes the families incidents
    def encode_families(families):

        name_to_letter = {}
        available_letters = list(string.ascii_uppercase)
        #print("Available letters:", available_letters)

        for idx, name in enumerate(families):
            #print("Name:", name)
            if available_letters:
                letter = available_letters.pop(0)
            else:
                if idx < 26 + 26 * 26:
                    combinations = itertools.product(
                        string.ascii_uppercase, repeat=2
                        )  # Two-letter combinations (AA, AB, ..., ZZ)
                    for combo in combinations:
                        if "".join(combo) not in name_to_letter.values():
                            letter = "".join(combo)
                            break
                else:
                    raise ValueError("Maximum number of encodings reached.")
            #print("Encoding:", letter)
            name_to_letter[letter] = name

        #encoded_names = [name_to_letter[name] for name in families]
        #print(encoded_names)
        return name_to_letter
            
    # Sets the seed
    def set_seed(seed):
        
        if seed != None:
            np.random.seed(seed)
            random.seed(seed)        
            
    # Gets the time spent by a function
    def get_function_time_spent(curr_time):
        
        end = datetime.now()
        time_delta = end - curr_time
        wait_time = time_delta.total_seconds()
        curr_time = end

        return wait_time, curr_time
    
    # Stores the generator data into a JSON file
    def save_generator_data(output_path, family_info, family_steps, subfamily_info, analysts_steps_info, special_steps):

        with open(output_path, 'w') as fd:
            fd.write(json.dumps([family_info, family_steps, subfamily_info, analysts_steps_info, special_steps], indent=2, default=str)) 

        print("Generator's info saved")
        
    # Creates log files for debugging purposes
    def create_log(path, name, active):
        
        log_file = f'{path}/{name}.txt'
        logger = logging.getLogger(name)
# =============================================================================
#         parent_logger = logger.parent
#         if parent_logger:
#             print(f"Parent logger name: {parent_logger.name}")
#         else:
#             print("No parent logger found (root logger)")
# =============================================================================
        
        if logger.hasHandlers():
            #print("Logger with the same name exists!")
            logger.handlers = []
            logger.setLevel(logging.NOTSET)
            
        if active:
            print("Logger Active")
            file_handler = logging.FileHandler(log_file, mode = 'w')
            #buffer_handler = BufferedFileHandler(log_file, mode='w', buffer_size=100000)
            #formatter = logging.Formatter('%(asctime)s - %(message)s')
            formatter = logging.Formatter('%(message)s')
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)  
            logger.setLevel(logging.INFO)
            #logging.basicConfig(level=logging.INFO)   
        else:
            print("Logger Disabled")
        
        #effective_level = logger.getEffectiveLevel()
        #print(f"The effective log level for the logger is {effective_level}")
        logger.propagate = False

        return logger
            
    # Gets famiies subtechniques (excluding locked subtechniques)
    def get_family_middle_subtechniques(family_steps_pool):
        
        family_subtechniques = {}
        
        for team in family_steps_pool:
            family_subtechniques[team] = {}
            for family in family_steps_pool[team]:
                family_subtechniques[team][family] = {}
                for main_step in family_steps_pool[team][family]:
                    if main_step != "other_steps" and main_step != "transfer_opt":
                        for secondary_step in family_steps_pool[team][family][main_step]:
                            family_subtechniques[team][family][secondary_step] = family_steps_pool[team][family][main_step][secondary_step]
                            
        return family_subtechniques
    
    #Get the special actions (start, end and transfer)
    def get_locked_techniques(special_steps):
        
        #print("Special_steps:", special_steps)
        if not isinstance(special_steps["init_opt"], list): 
            locked = list(special_steps["init_opt"].keys()) + list(special_steps["end_opt"].keys()) + list(special_steps["transfer_opt"].keys())
            for opt in special_steps["init_opt"].values():
                locked+= list(opt.keys())
            #print("Initial", locked)
            for opt in special_steps["end_opt"].values():
                locked+= list(opt.keys())
            #print("Final", locked)
        else:
            locked = special_steps["init_opt"] + special_steps["end_opt"] + special_steps["transfer_opt"]
            #print("List")
        
        return locked
    
    # Gets the shift where the ticket date is located, assuming 3 shifts: 0: 00h-07h59, 1: 08h-15h59, and 2: 16h-23h59
    def get_ticket_shift(curr_time):
        
        if Utils.check_date_between(time(0, 0, 0, 0), time(7, 59, 59, 999999), curr_time):
            return 0
        elif Utils.check_date_between(time(8, 0, 0, 0), time(15, 59, 59, 999999), curr_time):
            return 1
        else:
            return 2
            
    # Gets operators working in a particular shift
    def get_operators_in_shift(team_data, ticket_shift):
        
        analysts = []
        for analyst in team_data["analysts"]:
            if team_data["analysts"][analyst]["shift"] == ticket_shift:
                if team_data["analysts"][analyst]["active"]:
                    analysts.append(analyst)

        #print("analysts in shift:", analysts)
        return analysts
            
    # Prepares the analysts of the next shift and cleans data from analysts of the shift closed
    def update_analysts_in_next_shift(analysts_data, team, start_date, prev_shift, curr_shift, gen_analysts_info, tt_analysts_info, shifts_data, aux_data):

        if prev_shift != curr_shift:            
            for analyst in analysts_data:
                if analysts_data[analyst]["shift"] == prev_shift:
                    if gen_analysts_info != None:
                        #Utils.update_data(gen_analysts_info[team]["analysts"][analyst], assigned_ticket = None, fixed_tsp = None, fixed = None)
                        Utils.update_data(gen_analysts_info[team]["analysts"][analyst], assigned_ticket = None)
                    if tt_analysts_info != None:
                        #Utils.update_data(tt_analysts_info[team]["analysts"][analyst], assigned_ticket = None, fixed_tsp = None, fixed = None)
                        Utils.update_data(tt_analysts_info[team]["analysts"][analyst], assigned_ticket = None)

            start_date_utc, start_date_tsp = Utils.set_date_start_shift(start_date, shifts_data)
        
            for analyst in analysts_data:
                if analysts_data[analyst]["shift"] == curr_shift:
                    if gen_analysts_info != None:
                        #Utils.update_data(gen_analysts_info[team]["analysts"][analyst], assigned_ticket = None, fixed_tsp = None, fixed = None)
                        Utils.update_data(gen_analysts_info[team]["analysts"][analyst], fixed = start_date_utc, fixed_tsp = start_date_tsp, assigned_ticket = None)
                    if tt_analysts_info != None:
                        #Utils.update_data(tt_analysts_info[team]["analysts"][analyst], assigned_ticket = None, fixed_tsp = None, fixed = None)
                        Utils.update_data(tt_analysts_info[team]["analysts"][analyst], fixed = start_date_utc, fixed_tsp = start_date_tsp, assigned_ticket = None)
            
    # Checks for similar and coordinated tickets
    def check_similar_coordinated_tickets(ticket, tickets_data, tickets_inheritance, subfamily_pool, generation, aux_data):
    
        ticket_id = ticket["id"]
        client= ticket["client"]
        subfamily= ticket["subfamily"]
        datetime_raised= ticket["raised"]
        #country= ticket["country"]
        
        if generation:
            ticket["similar"] = []
            ticket["coordinated"] = []  
    
        if client not in tickets_inheritance:
            #print("New client:", client)
            tickets_inheritance[client] = {}
            
        if subfamily not in tickets_inheritance[client]:
            #print("New subfamily:", subfamily)
            tickets_inheritance[client][subfamily] = {}
            end_date = datetime_raised + timedelta(minutes = subfamily_pool[subfamily]["timerange"])
            Utils.update_data(tickets_inheritance[client][subfamily], start = datetime_raised, end = end_date, curr_counter =  1)
            tickets_inheritance[client][subfamily]["similar"], tickets_inheritance[client][subfamily]["similar_ids"] = [], []
            tickets_inheritance[client][subfamily]["similar"].append(ticket_id)
            tickets_inheritance[client][subfamily]["similar_ids"].append(ticket_id)
        else:
            #print("Subfamily already exists")
            if tickets_inheritance[client][subfamily]["start"] <= datetime_raised <= tickets_inheritance[client][subfamily]["end"]:    
                if generation:
                    ticket["similar"] = list(tickets_inheritance[client][subfamily]["similar"])
                    ticket["similar_ids"] = list(tickets_inheritance[client][subfamily]["similar_ids"])
                    #print("Similar:",ticket["similar"])
                    #print("Similar ids:",ticket["similar_ids"])
# =============================================================================
#                     coordinated_tickets = []
#                     for l in tickets_inheritance[client][subfamily]["similar"]:
#                         if country == tickets_data[l]["country"]:
#                             coordinated_tickets.append(tickets_data[l]["id"])
#                     
#                     if not coordinated_tickets:
#                         ticket["coordinated"] = "---"
#                     else:
#                         ticket["coordinated"] = coordinated_tickets
# =============================================================================

                tickets_inheritance[client][subfamily]["curr_counter"] += 1
            else:
                end_date = datetime_raised + timedelta(minutes = subfamily_pool[subfamily]["timerange"])
                Utils.update_data(tickets_inheritance[client][subfamily], start = datetime_raised, end = end_date, curr_counter =  1)
                tickets_inheritance[client][subfamily]["similar"], tickets_inheritance[client][subfamily]["similar_ids"] = [], [] 
            
            tickets_inheritance[client][subfamily]["similar"].append(ticket_id)
            tickets_inheritance[client][subfamily]["similar_ids"].append(ticket_id)
 
            if tickets_inheritance[client][subfamily]["curr_counter"] == subfamily_pool[subfamily]["max_counter"]:
                del tickets_inheritance[client][subfamily]
                Utils.debug_and_log_data(aux_data.debug, aux_data.logger, "Ticket should be replicated due to Max similarity!")
                ticket["replication_status"] = "Max similarity"
                ticket["status"] = "Transfer"            
            
    # Updates the data pertaining an analyst in a team
    def update_analyst_data(ticket, train_id, teams_data):
        
        team = ticket["team"]
        analyst = ticket["analyst"]
        
        Utils.update_data(teams_data[team]["analysts"][analyst], assigned_ticket = ticket["id"], fixed = ticket['fixed'], fixed_tsp = round(ticket["fixed_tsp"], 1))
        teams_data[team]["analysts"][analyst]["summary"][train_id] = ticket["duration_outlier"]
            
    # Updates the content of a variable
    def update_data(variable, **kwargs):        
        variable.update(kwargs)
            
    # Removes a tickets from priority queue after being closed by analyst
    def remove_ticket_priority_queue(ticket, priority_queues):
        
        ticket_id = ticket["id"]
        if ticket_id in priority_queues[ticket["team"]][ticket["priority"]]["tickets"]:
            priority_queues[ticket["team"]][ticket["priority"]]["tickets"].remove(ticket_id)
            
    # Frees the analyst when ticket is fixed
    def check_pending_tickets_priorities(analysts_info, analysts_in_shift, curr_team, ticket_tsp, tickets_info, priority_queues, aux_data):

        if Utils.check_tickets_in_team_queue(priority_queues, curr_team):
            min_time, min_tsp = Utils.find_min_analyst_endtime(analysts_info[curr_team]["analysts"], analysts_in_shift, aux_data)
            Utils.update_tickets_wait_time(curr_team, min_tsp, tickets_info, priority_queues, aux_data)
            Utils.update_tickets_priorities(curr_team, tickets_info, priority_queues, min_time, min_tsp, aux_data)

    # Updates the wait time of the pending tickets
    def update_tickets_wait_time(team, min_curr_tsp, tickets_info, priority_queues, aux_data):
            
        for priority in priority_queues[team]:
            if priority != aux_data.priority_levels: # No need to update the tickets with max priority since there are no greater levels
                Utils.debug_and_log_data(aux_data.debug, aux_data.logger, f'Priority studied {priority}')
                if priority_queues[team][priority]["tickets"]:
                    Utils.debug_and_log_data(aux_data.debug, aux_data.logger, f'Update pending tickets wait time in team {team} with priority {priority}')
                    for ticket_id in priority_queues[team][priority]["tickets"]:
                        time_in_queue = Utils.calculate_timestamp_diff(tickets_info[ticket_id]['added_queue_tsp'], min_curr_tsp, "minutes")    
                        tickets_info[ticket_id]['in_queue'] = time_in_queue

    # Updates the priorities of the tickets          
    def update_tickets_priorities(team, tickets_info, priority_queues, min_time, min_time_tsp, aux_data):

        Utils.debug_and_log_data(aux_data.debug, aux_data.logger, f'Priorities queue BEFORE: {priority_queues}')
        priorities_changed, new_priority_team = {}, {}
        Utils.instantiate_priority_queues(aux_data.priority_levels, new_priority_team)
           
        for priority in priority_queues[team]:
            if priority_queues[team][priority]["tickets"]:                
                Utils.debug_and_log_data(aux_data.debug, aux_data.logger, f'Curr Priority: {priority}')

                if priority == aux_data.priority_levels:
                    if new_priority_team[priority]["tickets"]:
                        new_priority_team[priority]["tickets"] = new_priority_team[priority]["tickets"] + list(priority_queues[team][priority]["tickets"])
                    
                        sorted_id_list = Utils.sort_priority_tickets(new_priority_team[priority]["tickets"], tickets_info, aux_data)
                        if sorted_id_list != None:
                            new_priority_team[priority]["tickets"] = sorted_id_list
                            Utils.debug_and_log_data(aux_data.debug, aux_data.logger, f'After in max priority: {new_priority_team[priority]["tickets"]}')
                    else:
                        Utils.update_data(new_priority_team[priority], tickets = list(priority_queues[team][priority]["tickets"]))
                else:
                    avg = Utils.get_last_n_tickets_in_priority_queue(priority_queues[team][priority]["tickets"], tickets_info, 5, 2, aux_data.logger)
                    if avg == None:
                        if new_priority_team[priority]["tickets"]:
                            new_priority_team[priority]["tickets"] = new_priority_team[priority]["tickets"] + list(priority_queues[team][priority]["tickets"])
                        else:
                            Utils.update_data(new_priority_team[priority], tickets = list(priority_queues[team][priority]["tickets"]))
                    else:
                        Utils.debug_and_log_data(aux_data.debug, aux_data.logger, f'Avg of the last {5} tickets in priority {priority} with multiplier {2} is {avg}')
                        for ticket_id in priority_queues[team][priority]["tickets"]:    
                            if tickets_info[ticket_id]['in_queue'] >= avg: 
                                next_priority = Utils.get_next_priority(priority, aux_data.priority_levels)
                                Utils.debug_and_log_data(aux_data.debug, aux_data.logger, f'Ticket {ticket_id} will be moved to priority {next_priority}')
                                new_priority_team[next_priority]["tickets"].append(ticket_id)
                                Utils.debug_and_log_data(aux_data.debug, aux_data.logger, f'Ticket {ticket_id} is in queue since {tickets_info[ticket_id]["in_queue"]} minutes')
                                        
                                tickets_info[ticket_id]['priority'] = next_priority
                                tickets_info[ticket_id]['added_queue_time'] = min_time
                                tickets_info[ticket_id]['added_queue_tsp'] = min_time_tsp
                                
                                if next_priority not in priorities_changed:
                                    priorities_changed[next_priority] = []
                                    
                                if ticket_id not in priorities_changed[next_priority]:
                                    priorities_changed[next_priority].append(ticket_id)
                            else:
                                Utils.debug_and_log_data(aux_data.debug, aux_data.logger, f'Ticket {ticket_id} queue time {tickets_info[ticket_id]["in_queue"]} is below {avg}')
                                new_priority_team[priority]["tickets"].append(ticket_id)

        #print(f'Priorities queue before: {priority_queues[team]}')
        priority_queues[team] = new_priority_team
        
        if priorities_changed:
            Utils.debug_and_log_data(aux_data.debug, aux_data.logger, f'Tickets were added to priorities {priorities_changed}')
            for priority in priorities_changed:
                sorted_id_list = Utils.sort_priority_tickets(priority_queues[team][priority]["tickets"], tickets_info, aux_data.logger)
                if sorted_id_list != None:
                    Utils.debug_and_log_data(aux_data.debug, aux_data.logger, f'Before {team} {priority}: {priority_queues[team][priority]["tickets"]}')
                    priority_queues[team][priority]["tickets"] = sorted_id_list
                    Utils.debug_and_log_data(aux_data.debug, aux_data.logger, f'After {team} {priority}: {priority_queues[team][priority]["tickets"]}')
            
            Utils.debug_and_log_data(aux_data.debug, aux_data.logger, f'Priorities queue AFTER: {priority_queues}')
         
    # Updates allocation times of the pending tickets                   
    def update_allocated_times(tickets_info, priority_queues, team, min_curr_time, min_curr_tsp, aux_data):
        
        Utils.debug_and_log_data(aux_data.debug, aux_data.logger, f'Curr priorities {priority_queues[team]}')
        for priority in priority_queues[team]:
            if priority_queues[team][priority]["tickets"]:
                for ticket_id in priority_queues[team][priority]["tickets"]:
                    if min_curr_tsp > tickets_info[ticket_id]['allocated_tsp']:
                        Utils.update_data(tickets_info[ticket_id], allocated = min_curr_time, allocated_tsp = min_curr_tsp, temp_allocated = min_curr_time, temp_allocated_tsp = min_curr_tsp)
                        Utils.debug_and_log_data(aux_data.debug, aux_data.logger, f'ticket {ticket_id} allocated updated: {tickets_info[ticket_id]["allocated"]}')
                        if "analysed_in_shift" in tickets_info[ticket_id]:
                            del tickets_info[ticket_id]['analysed_in_shift']
                            
    # Creates the priority queues that will store the pending tickets  
    def instantiate_priority_queues(priority_levels, team_priority_queues):
        
        for priority in range(1, priority_levels + 1):
            team_priority_queues[priority] = {}
            team_priority_queues[priority]["tickets"] = []
            
    # Updates family's resolution times and other statistics
    def update_family_resolution(ticket, families_resolution):
        
        team = ticket["team"]
        family = ticket["family"]
        duration = ticket["duration_outlier"]
        
        if team not in families_resolution:
            families_resolution[team] = {}
        if family not in families_resolution[team]:
            families_resolution[team][family] = {}
            families_resolution[team][family]["number"], families_resolution[team][family]["total_time"], families_resolution[team][family]["avg_time"] = 0, 0, 0
            
        families_resolution[team][family]["number"] += 1
        families_resolution[team][family]["total_time"] += duration
        families_resolution[team][family]["avg_time"] = families_resolution[team][family]["total_time"] / families_resolution[team][family]["number"]
        
    # Replicates and escalates a ticket to the next team
    def replicate_ticket(teams_data, original_ticket, tickets, priority_queues, n_replicated, in_generation, aux_data):
        
        team = original_ticket["team"]
        ticket_id = original_ticket["id"]
        #print("Ticket:", original_ticket)
    
        if team != "L4":
            n_replicated += 1
            next_team = Utils.get_next_team(team, list(teams_data))

            next_id = len(tickets[next_team])
            #print("Next_id:", next_id)
            tickets[next_team][next_id] = {}
            rep_ticket = tickets[next_team][next_id]
            rep_ticket["id"] = next_id

            Utils.update_data(rep_ticket, raised = original_ticket["fixed"], raised_tsp = original_ticket["fixed_tsp"], allocated = original_ticket["fixed"], allocated_tsp = original_ticket["fixed_tsp"], team = next_team, analyst = "---")
            Utils.update_data(rep_ticket, country = original_ticket["country"], client =  original_ticket["client"], family = original_ticket["family"], subfamily = original_ticket["subfamily"], priority = original_ticket["priority"], outlier = original_ticket["outlier"], replicated = ticket_id, escalate = False)

            substr = ['feature', 'source', 'destination']
            filtered_features = Utils.filter_string(list(original_ticket.keys()), substr)
            #print("Filtered features", filtered_features)
            for feature in filtered_features:
                #print("Feature:", feature)
                rep_ticket[feature] = original_ticket[feature]

            if "new_family" in original_ticket:
                Utils.update_data(rep_ticket, new_family = original_ticket["new_family"])
                
            if "new_subfamily" in original_ticket:
                Utils.update_data(rep_ticket, new_subfamily = original_ticket["new_subfamily"])
                
            if not in_generation:
                Utils.update_data(rep_ticket, similar_subfamilies = original_ticket["similar_subfamilies"], init_priority = original_ticket["init_priority"])
            
            Utils.debug_and_log_data(aux_data.debug, aux_data.logger, f'N replicated_tickets: {n_replicated} in {team}. New ticket was added to upper teams: {priority_queues[next_team][original_ticket["priority"]]["tickets"]}')
        else:
            Utils.debug_and_log_data(aux_data.debug, aux_data.logger, "Can't be replicated because it is already on the top team")
    
        return n_replicated
    
    # Gets the data of the next ticket to be analysed
    def get_next_ticket(ticket, close_shift, curr_shift, analysts_in_shift, original_dict_idx, tickets, original_keys, analysts_info, priority_queues, families_resolution, shifts_data, aux_data):

        if Utils.check_tickets_in_team_queue(priority_queues, ticket["team"]):
            Utils.debug_and_log_data(aux_data.debug, aux_data.logger, f'Priority queue {priority_queues}. Shift: {curr_shift}')
            next_ticket_id, temp_date, temp_tsp, highest_priority_ticket_id = Utils.get_next_pending_ticket(ticket, analysts_info, analysts_in_shift, priority_queues[ticket["team"]], tickets, close_shift, families_resolution, shifts_data[curr_shift], aux_data)
            
            update_ticket = True
            if "analysed_in_shift" in tickets[next_ticket_id]:
                Utils.debug_and_log_data(aux_data.debug, aux_data.logger, f'id {next_ticket_id} was analysed in shift {curr_shift}')
                update_ticket = False
                
            Utils.debug_and_log_data(aux_data.debug, aux_data.logger, f'Update_ticket: {update_ticket}')

            if original_dict_idx + 1 >= len(original_keys):
                Utils.debug_and_log_data(aux_data.debug, aux_data.logger, f'Original data already read!. Next_id {next_ticket_id} - {tickets[next_ticket_id]["allocated"]}')
                
                if update_ticket:
                    tickets[next_ticket_id]["allocated"] = temp_date
                    tickets[next_ticket_id]["allocated_tsp"] = temp_tsp
                    Utils.debug_and_log_data(aux_data.debug, aux_data.logger, f'Test ticket {next_ticket_id} in {temp_date}')
                    return next_ticket_id, original_dict_idx, curr_shift, analysts_in_shift
                else:
                    pending_shift = Utils.get_ticket_shift(temp_date.time())
                    next_ticket_date, next_shift = Utils.get_next_shift_data(temp_date, pending_shift)   
                    Utils.update_allocated_times(tickets, priority_queues, ticket["team"], next_ticket_date, next_ticket_date.timestamp(), aux_data) 
                    analysts_in_next_shift = Utils.get_operators_in_shift(analysts_info[ticket["team"]], next_shift)
                    #print(f'Ticket {next_ticket_id} i scheduled for {next_ticket_date} on shift {next_shift} with operators {analysts_in_next_shift}')
                    Utils.debug_and_log_data(aux_data.debug, aux_data.logger, f'Pending tickets are going to be analysed in {next_ticket_date} on shift {next_shift} with operators {analysts_in_next_shift}')
                    return next_ticket_id, original_dict_idx, next_shift, analysts_in_next_shift
            else:
                next_original_key = original_keys[original_dict_idx + 1]
                next_original_ticket_date = tickets[next_original_key]["raised"] 

                Utils.debug_and_log_data(aux_data.debug, aux_data.logger, f'Pending date: {temp_date}. Next original ticket: {tickets[next_original_key]["raised"]}')
                
                if temp_date <= next_original_ticket_date:
                    pending_shift = Utils.get_ticket_shift(temp_date.time())
                    next_original_shift = Utils.get_ticket_shift(next_original_ticket_date.time())
                    if pending_shift != next_original_shift or (pending_shift == next_original_shift and next_original_ticket_date.day != temp_date.day):
                        if next_ticket_id == highest_priority_ticket_id and not update_ticket:
                            next_ticket_date, next_shift = Utils.get_next_shift_data(temp_date, curr_shift)   
                            Utils.update_allocated_times(tickets, priority_queues, ticket["team"], next_ticket_date, next_ticket_date.timestamp(), aux_data) 
                            analysts_in_next_shift = Utils.get_operators_in_shift(analysts_info[ticket["team"]], next_shift)
                            #print(f'Ticket {next_ticket_id} i scheduled for {next_ticket_date} on shift {next_shift} with operators {analysts_in_next_shift}')
                            Utils.debug_and_log_data(aux_data.debug, aux_data.logger, f'Pending tickets are going to be analysed in {next_ticket_date} on shift {next_shift} with operators {analysts_in_next_shift}')
                            return next_ticket_id, original_dict_idx, next_shift, analysts_in_next_shift

                        tickets[next_ticket_id]["allocated"] = temp_date
                        tickets[next_ticket_id]["allocated_tsp"] = temp_tsp
                        Utils.debug_and_log_data(aux_data.debug, aux_data.logger, f'Test ticket {next_ticket_id} in {temp_date}')
                                
                        if Utils.get_ticket_shift(tickets[next_ticket_id]["allocated"].time()) != curr_shift:
                            next_shift = Utils.get_next_shift(Utils.get_ticket_shift(tickets[next_ticket_id]["allocated"].time()))
                            Utils.debug_and_log_data(aux_data.debug, aux_data.logger, f'next_shift {next_shift}')
                            analysts_in_next_shift = Utils.get_operators_in_shift(analysts_info[ticket["team"]], next_shift)
                            return next_ticket_id, original_dict_idx, next_shift, analysts_in_next_shift
                        else:
                            return next_ticket_id, original_dict_idx, curr_shift, analysts_in_shift
                    else:
                        if update_ticket:
                            tickets[next_ticket_id]["allocated"] = temp_date
                            tickets[next_ticket_id]["allocated_tsp"] = temp_tsp
                            Utils.debug_and_log_data(aux_data.debug, aux_data.logger, f'Test ticket {next_ticket_id} in {temp_date}')
                            
                            if Utils.get_ticket_shift(tickets[next_ticket_id]["allocated"].time()) != curr_shift:
                                next_shift = Utils.get_next_shift(Utils.get_ticket_shift(tickets[next_ticket_id]["allocated"].time()))
                                Utils.debug_and_log_data(aux_data.debug, aux_data.logger, f'next_shift {next_shift}')
                                analysts_in_next_shift = Utils.get_operators_in_shift(analysts_info[ticket["team"]], next_shift)
                                return next_ticket_id, original_dict_idx, next_shift, analysts_in_next_shift
                            else:
                                return next_ticket_id, original_dict_idx, curr_shift, analysts_in_shift

        if bool(tickets) and original_dict_idx + 1 < len(tickets):
            original_dict_idx += 1
            next_id = original_keys[original_dict_idx]
            if Utils.get_ticket_shift(tickets[next_id]["allocated"].time()) != curr_shift:
                next_shift = Utils.get_ticket_shift(tickets[next_id]["allocated"].time())
                Utils.debug_and_log_data(aux_data.debug, aux_data.logger, f'next_shift {next_shift}')
                analysts_in_next_shift = Utils.get_operators_in_shift(analysts_info[ticket["team"]], next_shift)
                return next_id, original_dict_idx, next_shift, analysts_in_next_shift
                
            Utils.debug_and_log_data(aux_data.debug, aux_data.logger, f'Ticket id {next_id} is read from original_dict')
            #print(f'Next ticket id {next_id} is read from original_dict. Index {original_dict_idx}')
        else:
            next_id = None

        return next_id, original_dict_idx, curr_shift, analysts_in_shift
    
    # Verifies if there are pending tickets, assigned to a particular team
    def check_tickets_in_team_queue(priority_queues, team):

        for priority in priority_queues[team]:
            if priority_queues[team][priority]["tickets"]:
                return True
        
        return False
    
    # Gets the next shift
    def get_next_shift(curr_shift):
        
        next_shift = -1
        if curr_shift == 2:
            next_shift = 0
        elif curr_shift == 1:
            next_shift = 2
        else:
            next_shift = 1
            
        return next_shift
    
    # Gets information about the next shift
    def get_next_shift_data(temp_date, curr_shift):
        
        next_shift = Utils.get_next_shift(curr_shift)
        #print("Next shift:", next_shift)
        if next_shift == 0:
            #print("Shift is on next day!")
            temp_date = Utils.update_date(temp_date, next_shift)
            temp_date = temp_date + timedelta(1)
        else:
            temp_date = Utils.update_date(temp_date, next_shift)
            
        #ticket_week_day = calendar.day_name[temp_date.weekday()]
        return temp_date, next_shift
    
    # Updates a datetime
    def update_date(date, next_shift):
        
        next_date = ""
        if next_shift == 0:
            next_date = date.replace(minute = 00, hour = 00, second = 00, microsecond = 0, year = date.year, month = date.month, day = date.day)
        elif next_shift == 1:
            next_date = date.replace(minute = 00, hour = 8, second = 00, microsecond = 0, year = date.year, month = date.month, day = date.day)
        else:
            next_date = date.replace(minute = 00, hour = 16, second = 00, microsecond = 0, year = date.year, month = date.month, day = date.day)
    
        return next_date
    
    # Checks if a date is between other two dates
    def check_date_between(begin_time, end_time, check_time=None):
    
        # If check time is not given, default to current UTC time
        check_time = check_time or datetime.utcnow().time()
        if begin_time < end_time:
            return check_time >= begin_time and check_time <= end_time
        else: # crosses midnight
            return check_time >= begin_time or check_time <= end_time  
        
    # Sets the starting date of the last of a shift
    def set_date_start_shift(start_date, shifts_data):
        
        start_date_date = start_date.date()
        start_date_shift = Utils.get_ticket_shift(start_date.time())
        start_date_time = datetime.strptime(shifts_data[start_date_shift]["start"], "%H:%M:%S.%f").time()
        start_date_combined = datetime.combine(start_date_date, start_date_time)
        start_date_combined_utc = pytz.UTC.localize(start_date_combined)
        
        return start_date_combined_utc, start_date_combined_utc.timestamp()
    
    # Gets the analysts available at a particular timestamp
    def get_free_analysts_tsp(analysts_info, analysts, ticket_tsp, aux_data):

        free_analysts = []
        #print("Users in shift:", analysts)
        for analyst in analysts:
            if analysts_info[analyst]["fixed_tsp"] <= ticket_tsp: 
                free_analysts.append(analyst)
            else:
                Utils.debug_and_log_data(aux_data.debug, aux_data.logger, f'{analyst} occupied until {analysts_info[analyst]["fixed"]}')
                
        if not free_analysts:
            Utils.debug_and_log_data(aux_data.debug, aux_data.logger, "No analysts available at the moment!")
        else:
            Utils.debug_and_log_data(aux_data.debug, aux_data.logger, f'Analysts available: {free_analysts}')

        return free_analysts
    
    # Gets the earliest ending datetime of all analysts
    def find_min_analyst_endtime(analysts_data, analysts_in_shift, aux_data):
        
        min_time = None
        min_curr_tsp = float('inf')
        for analyst in analysts_in_shift:
            Utils.debug_and_log_data(aux_data.debug, aux_data.logger, f'{analyst} - {analysts_data[analyst]["fixed"]}')
            if min_curr_tsp >= analysts_data[analyst]["fixed_tsp"]:
                min_time = analysts_data[analyst]["fixed"]
                min_curr_tsp = analysts_data[analyst]["fixed_tsp"]
                
        #print("Min:", min_curr_tsp)
        return min_time, min_curr_tsp
    
    # Returns the differences between two dates (in minutes)
    def calculate_timestamp_diff(t1, t2, time_unit):

        diff_seconds = abs(t2 - t1)
        if time_unit == "seconds":
            #print("Difference (seconds):", diff_seconds)
            return diff_seconds
        elif time_unit == "minutes":
            diff_minutes = diff_seconds / 60
            #print("Difference (minutes):", diff_minutes)
            return diff_minutes
        else:
            diff_hours = diff_seconds / 3600
            #print("Difference (hours):", diff_hours)
            return diff_hours
        
    # Sorts the pending tickets of a particular priority
    def sort_priority_tickets(tickets, tickets_info, aux_data):
        
        sorted_id_list = None
        if tickets and not Utils.is_sorted_by_datetime(tickets, tickets_info):
            sorted_id_list = sorted(tickets, key=lambda item: tickets_info[item]["raised_tsp"])
            Utils.debug_and_log_data(aux_data.debug, aux_data.logger, f'Sorted tickets ids: {sorted_id_list}') 
            
        return sorted_id_list
    
    # Calculates the average wait time of each priority queue based on the last n tickets (the multiplier helps assign a limit wait time per priority level)
    def get_last_n_tickets_in_priority_queue(priority_queue, tickets_info, n_tickets, multiplier, logger):
        
        avg = None
        if len(priority_queue) > n_tickets:
            n_ticket_ids = priority_queue[-n_tickets:]
            n_total_in_queue = 0
            for ticket_id in n_ticket_ids:
                n_total_in_queue += tickets_info[ticket_id]['in_queue']
                
            avg = (n_total_in_queue / n_tickets) * multiplier
            
        return avg
    
    # Gets the next priority considering the current priority
    def get_next_priority(curr_priority, max_priority):
            
        if curr_priority < max_priority:
            return curr_priority + 1
        else:
            return curr_priority
        
    # Gets the next team
    def get_next_team(curr_team, all_teams):
        
        index = all_teams.index(curr_team)
        next_team = all_teams[index + 1]    
        #print("Next:", next_team)
        return next_team
    
    # Filters string
    def filter_string(string, substr):
        return [str for str in string if any(sub in str for sub in substr)]
    
    # Gets the next pending ticket from replicated and pending tickets
    def get_next_pending_ticket(ticket, analysts_info, analysts_in_shift, team_priority_queue, tickets, close_shift, families_resolution, shift_data, aux_data):

        min_time, min_tsp = None, None
        
        max_priority = Utils.get_highest_priority_with_tickets(team_priority_queue)
        min_time, min_tsp = Utils.find_min_analyst_endtime(analysts_info[ticket["team"]]["analysts"], analysts_in_shift, aux_data)
        highest_priority_ticket_id = team_priority_queue[max_priority]["tickets"][0]
        
        if close_shift:
            if ticket["id"] == highest_priority_ticket_id:
                Utils.debug_and_log_data(aux_data.debug, aux_data.logger, "Is the highest priority ticket")
            else:
                if ticket["id"] in team_priority_queue[ticket["priority"]]["tickets"]:
                    Utils.debug_and_log_data(aux_data.debug, aux_data.logger, f'Curr ticket id {ticket["id"]} is the ticket with lowest priority')
                else:
                    Utils.debug_and_log_data(aux_data.debug, aux_data.logger, "Curr ticket id was fixed")
            
            end_time = datetime.strptime(shift_data["end"], "%H:%M:%S.%f").time()
            end_datetime = datetime.combine(min_time.date(), end_time)
            end_datetime_utc = end_datetime.replace(tzinfo=pytz.UTC)
            end_datetime_tsp = end_datetime_utc.timestamp()
            
            remaining_time = Utils.calculate_timestamp_diff(end_datetime_tsp, min_tsp, "minutes")    
            
            ticket_id_index = 0
            next_ticket_id = Utils.get_next_ticket_id_pending(ticket_id_index, team_priority_queue, max_priority, tickets, families_resolution, remaining_time, aux_data)
            if next_ticket_id != None:
                return next_ticket_id, min_time, min_tsp, highest_priority_ticket_id
            
            next_priority = max_priority - 1
            if next_priority >= min(team_priority_queue): 
            
                ticket_id_index = 0
                while next_priority >= min(team_priority_queue): 
                    Utils.debug_and_log_data(aux_data.debug, aux_data.logger, f'Next priority {next_priority}')
                    if team_priority_queue[next_priority]["tickets"]:
                        Utils.debug_and_log_data(aux_data.debug, aux_data.logger, f'Number of tickets in the next priority {next_priority} is {len(team_priority_queue[next_priority]["tickets"])}')
                        next_ticket_id = Utils.get_next_ticket_id_pending(ticket_id_index, team_priority_queue, next_priority, tickets, families_resolution, remaining_time, aux_data)
                        if next_ticket_id != None:
                            return next_ticket_id, min_time, min_tsp, highest_priority_ticket_id
                        
                    next_priority = next_priority - 1
                    ticket_id_index = 0
            
            Utils.debug_and_log_data(aux_data.debug, aux_data.logger, "All pending tickets were verified")

        if min_time > tickets[highest_priority_ticket_id]["allocated"]:
            Utils.debug_and_log_data(aux_data.debug, aux_data.logger, f'Send the ticket with highest priority {highest_priority_ticket_id}. Use min analyst date: {min_time}')
            return highest_priority_ticket_id, min_time, min_tsp, highest_priority_ticket_id
        else:
            Utils.debug_and_log_data(aux_data.debug, aux_data.logger, f'Send the ticket with highest priority {highest_priority_ticket_id} with its date: {tickets[highest_priority_ticket_id]["allocated"]}')
            return highest_priority_ticket_id, tickets[highest_priority_ticket_id]["allocated"], tickets[highest_priority_ticket_id]["allocated_tsp"], highest_priority_ticket_id
        
    # Verifies if list of tickets is sorted by datetime
    def is_sorted_by_datetime(ticket_list, tickets_info):
        #print("Tickets to check:", ticket_list)
        for i in range(len(ticket_list) - 1):
            current_id = ticket_list[i]
            current_datetime = tickets_info[current_id]["raised_tsp"]
            next_id = ticket_list[i + 1]
            next_datetime = tickets_info[next_id]["raised_tsp"]
            
            if current_datetime > next_datetime:
                return False
        return True
    
    # Returns the most priority ticket
    def get_highest_priority_with_tickets(team_tickets):
        
        min_priority = min(team_tickets)
        max_priority = max(team_tickets)

        for priority in range(max_priority, min_priority -1 , -1):
            if team_tickets[priority]["tickets"]:
                return priority
            
        return None
    
    # Returns the least priority ticket
    def get_least_priority_ticket(team_tickets, logger):
        
        min_priority = min(team_tickets)
        max_priority = max(team_tickets)
        
        for priority in range(min_priority, max_priority + 1, 1):
            if team_tickets[priority]["tickets"]:
                return priority, team_tickets[priority]["tickets"][-1]
            
    # Delivers the next ticket id waiting for treatment
    def get_next_ticket_id_pending(ticket_id_index, team_priority_queue, priority, tickets, families_resolution, remaining_time, aux_data):
        
        while True:
            if ticket_id_index < len(team_priority_queue[priority]["tickets"]):
                temp_ticket_id = team_priority_queue[priority]["tickets"][ticket_id_index]
                if "analysed_in_shift" not in tickets[temp_ticket_id]:
                    if tickets[temp_ticket_id]["family"] in families_resolution:
                        if families_resolution[tickets[temp_ticket_id]["family"]]["avg_time"] < remaining_time:
                            Utils.debug_and_log_data(aux_data.debug, aux_data.logger, f'Check next id is {temp_ticket_id} from priority {priority}')
                            return temp_ticket_id
                        else:
                            Utils.debug_and_log_data(aux_data.debug, aux_data.logger, f'Next id should not be analysed now since the average is {families_resolution[tickets[temp_ticket_id]["family"]]["avg_time"]}')
                    else:
                        Utils.debug_and_log_data(aux_data.debug, aux_data.logger, f'Check next id is {temp_ticket_id} from priority {priority}. Not registed in families resolution')
                        return temp_ticket_id
                #else:
                #    Utils.debug_and_log_data(aux_data.debug, aux_data.logger, f'Id {temp_ticket_id} from priority {priority} already checked in the past')
            else:
                break
            ticket_id_index += 1
            
        return None
    
    # Creates a dataframe from all tickets treated by the different teams (if other teams besides the baseline one treated tickets)
    def process_tickets_solved(tickets, teams, subfamily_pool, generation, aux_data):
        
        if len(tickets) == 1:
            #print("Only one team")
            return tickets[list(tickets.keys())[0]]
        else:
            #print("Teams to merge:", tickets.keys())
            return Utils.merge_team_tickets(tickets, teams, subfamily_pool, generation, aux_data)
        
    # Verifies if the next teams have tickets to solve
    def check_next_existing_teams(tickets, team):
        
        next_teams = Utils.get_remaining_teams(team, list(tickets))         
        if next_teams:
            if not tickets[next_teams[0]]:
                for remove_team in next_teams:
                    if not tickets[remove_team]:
                        #print("No tickets in:", remove_team)
                        del tickets[remove_team]
            else:
                if not Utils.is_dict_sorted(tickets[next_teams[0]]):
                    #print("Not sorted")
                    sorted_items = sorted(tickets[next_teams[0]].items(), key=lambda x: x[1]['raised_tsp'])
                    tickets[next_teams[0]] = {i: value for i, (key, value) in enumerate(sorted_items)}
                    
    # Creates a dataframe with all tickets treated
    def merge_team_tickets(all_tickets, all_teams, subfamily_pool, generation, aux_data):
        
        new_dict, replicated_tickets, tickets_inheritance = {}, {}, {}
        curr_id, n_replicated = 0, 0
        #print("All_teams:", all_teams)
        
        while Utils.check_teams_tickets(all_tickets):
            #print("Final id:", curr_id)
            key, next_ticket, team = Utils.get_next_ticket_different_teams(all_tickets)
            new_dict[curr_id] = next_ticket
            new_dict[curr_id]["id"] = curr_id
            
            if team == all_teams[0]:
                next_team = Utils.get_next_team(team, list(all_teams))
                if next_team not in replicated_tickets:
                    replicated_tickets[next_team] = []
                    
                if generation:
                    Utils.check_similar_coordinated_tickets(new_dict[curr_id], new_dict, tickets_inheritance, subfamily_pool, generation, aux_data)
                     
            if team != all_teams[0]:
                if team not in replicated_tickets:
                    replicated_tickets[team] = []
                    
                if team == all_teams[1]:
                    next_teams = Utils.get_next_teams(team, list(replicated_tickets.keys()))
                    total_replicated_tickets = []
                    for next_team in next_teams:
                        total_replicated_tickets.extend(replicated_tickets[next_team])

                    increment = Utils.get_increment_with_id_greater(next_ticket["replicated"] + n_replicated, total_replicated_tickets)
                    new_dict[curr_id]["replicated"] += increment
                else:
                    team_idx = all_teams.index(team)
                    prev_team = all_teams[team_idx-1]
                    for prev_ticket in replicated_tickets[prev_team]:
                        if new_dict[prev_ticket]["status"] == "Transfer":
                            if "analysed" not in new_dict[prev_ticket]:
                                new_dict[prev_ticket]["analysed"] = True
                                new_replicated_id = replicated_tickets[prev_team][-1]
                                new_dict[curr_id]["replicated"] = new_replicated_id
                                #print("New replicated from:", new_dict[curr_id]["replicated"])
                                break
                    
                replicated_tickets[team].append(curr_id)
                n_replicated += 1

            del all_tickets[team][key]
            curr_id += 1
            
        return new_dict
    
    # Calculates the duration of a certain action and its progression over the steps
    def get_action_duration(family, action, team, user, steps_data, family_steps_pool, family_subtechniques, aux_data):

        dur = 0
        transitions = []
        family_techniques = family_steps_pool[team][family]
        action = Utils.change_action_format(action)
        Utils.debug_and_log_data(aux_data.debug, aux_data.logger, f'Calculate action duration of {action}')

        for step in action:
            #print("Step:", step)
            if step in family_steps_pool[team][family]["transfer_opt"].keys():
                #Utils.debug_and_log_data(aux_data.debug, aux_data.logger, "Last step is a transfer operation")
                subtech_dur = family_steps_pool[team][family]["transfer_opt"][step]
            elif step in family_techniques["other_steps"].keys():
                #Utils.debug_and_log_data(aux_data.debug, aux_data.logger, "Step comes from other families")
                subtech_dur = family_techniques["other_steps"][step]
            else:
                subtech_dur = family_subtechniques[team][family][step]
    
            if user != None:  
                Utils.debug_and_log_data(aux_data.debug, aux_data.logger, f'Get duration of step {step} for {user}')
                step_speed = float(steps_data[step]["speed"])
                #Utils.debug_and_log_data(aux_data.debug, aux_data.logger, f'Base Duration: {subtech_dur}. Step Speed: {step_speed}')
                user_step_dur = Utils.get_user_step_range(subtech_dur, step_speed)
                #Utils.debug_and_log_data(aux_data.debug, aux_data.logger, f'Duration of step {step} executed by {user} is {user_step_dur}')
                dur = dur + user_step_dur
                transitions.append(user_step_dur)
            else:
                #Utils.debug_and_log_data(aux_data.debug, aux_data.logger, f'The duration of step {step} is {dur}')
                dur = dur + subtech_dur
                
        Utils.debug_and_log_data(aux_data.debug, aux_data.logger, f'Final duration: {round(dur, 2)}')
        return round(dur, 2), transitions
    
    # Gets the duration of an analyst-step
    def get_user_step_range(subtechnique_dur, speed):
    
        if speed < 1:
            max_step_dur = subtechnique_dur / speed
            min_step_dur = subtechnique_dur * speed
        else:            
            min_step_dur = subtechnique_dur / speed
            max_step_dur = subtechnique_dur * speed
        
        user_step_dur = random.uniform(min_step_dur, max_step_dur)
        return round(user_step_dur, 2)
    
    # Verifies whether the current shift is near its closure
    def check_close_sfift(team_priority_queue, tickets_info, aux_data):
        
        max_priority = Utils.get_highest_priority_with_tickets(team_priority_queue)
        #print("Max priority_:", max_priority)
        if max_priority != None:
            highest_priority_ticket_id = team_priority_queue[max_priority]["tickets"][0]
            if "analysed_in_shift" in tickets_info[highest_priority_ticket_id]:
                Utils.debug_and_log_data(aux_data.debug, aux_data.logger, "Highest priority ticket already analysed. Closed shift is set to true to review the remaining pending tickets")
                return True
            
        return False
    
    # Adds the ticket to its corresponding priority queue
    def send_ticket_priority_queue(ticket, priority_queues, aux_data, issue):
        
        if issue == 0:    
            Utils.debug_and_log_data(aux_data.debug, aux_data.logger, "Shift is almost ending. Add the ticket to the priority queue by the generator")
        elif issue == 1:
            Utils.debug_and_log_data(aux_data.debug, aux_data.logger, "At the moment, all analysts are occupied. Add the ticket to the priority queue by the generator")
        else:
            Utils.debug_and_log_data(aux_data.debug, aux_data.logger, "No one is working on current shift. Schedule for next shift")

        ticket_id = ticket["id"]
        if ticket_id not in priority_queues[ticket["team"]][ticket["priority"]]["tickets"]:
            priority_queues[ticket["team"]][ticket["priority"]]["tickets"].append(ticket_id)  
            ticket['added_queue_time'] = ticket['raised']
            ticket['added_queue_tsp'] = ticket['raised_tsp']
        else:
            Utils.update_data(ticket, allocated = ticket["temp_allocated"], allocated_tsp = ticket["temp_allocated_tsp"])
            Utils.debug_and_log_data(aux_data.debug, aux_data.logger, f'Ticket {ticket_id} already in priority_queue. Reset date to {ticket["temp_allocated"]}')
            Utils.debug_and_log_data(aux_data.debug, aux_data.logger, f'Reset time {ticket["temp_allocated"].time()}')
            
    # Checks the ticket status
    def check_ticket_distance(ticket, user_action, subfamily_action, actions_similarity, all_teams, ticket_verification):
        
        team = ticket["team"]
        distance = Utils.calculate_distance(user_action, subfamily_action)
        ticket["distance"] = distance

        if distance >= actions_similarity and ticket_verification:
            index = all_teams.index(team)
            if index <= 2:
                return "Transfer"
        return "Closed"
    
    # Updates the action and its duration according to its escalation status
    def convert_to_escaleted_action(ticket, action, transfer_data):

        action[-1] = transfer_data[0]
        #print("Prev action:", action)
        if len(action) > 2:
            action.pop(len(action) - 2)

        action_updated = ""
        for l in range(len(action)):
            action_updated += "'" + action[l] + "'"
               
        #print("Updated action:", action_updated)
        #self.subfamily_analysts_action[subfamily][user]['action'] = action_updated
        #print(f'The action updated was updated to {action_updated}')
        return Utils.change_action_format(action_updated)
    
    # Verifies if the time that it takes to fix a ticket surpasses the user shift
    def check_shift_ending(ticket_time_complete, action_dur, aux_data):
        
# =============================================================================
#         print("Ticket complete:", ticket_time_complete)
#         
#         is_utc = ticket_time_complete.tzinfo == pytz.utc  # or dt.tzinfo == pytz.utc
# 
#         if is_utc:
#             print("The datetime is in UTC.")
#         else:
#             print("The datetime is not in UTC.")
# =============================================================================
        
        current_hour = ticket_time_complete.hour
        curr_timestamp = ticket_time_complete.timestamp()
        next_timestamp = curr_timestamp + action_dur * 60
        next_time = datetime.utcfromtimestamp(next_timestamp)
        next_hour = next_time.hour

        if (current_hour == 6 and next_hour == 8) or (current_hour == 7 and next_hour == 8) or (current_hour == 7 and next_hour == 9) or (current_hour == 14 and next_hour == 16) or (current_hour == 15 and next_hour == 16) or (current_hour == 15 and next_hour == 17) or (current_hour == 22 and next_hour == 0) or (current_hour == 23 and next_hour == 0) or (current_hour == 23 and next_hour == 1) or (current_hour == 23 and next_hour == 2):
            Utils.debug_and_log_data(aux_data.debug, aux_data.logger, "Action will surpass the analyst's shift")
            return True
        else:
            return False
        
    # Generates actions for subfamilies and users
    def build_analyst_action(family, subfamily, team, member, action, steps_info, special_tech, aux_data):

        subtechniques = action.split("'")
        subtechniques_cleaned = [x for x in subtechniques if x]

        Utils.debug_and_log_data(aux_data.debug, aux_data.logger, f'Generate action for analyst {member} using the action {subtechniques_cleaned} in subfamily {subfamily}')

        operations_number = random.randint(2, 3)
        operations = random.choices(aux_data.action_operations, (0.85, 0.05, 0.05, 0.05), k = operations_number)
        
        while ('+' or '-' or '%') not in operations:
            operations = random.choices(aux_data.action_operations, (0.85, 0.05, 0.05, 0.05), k = operations_number)
            Utils.debug_and_log_data(aux_data.debug, aux_data.logger, f'Operations: {operations}')

        for opt in operations:      
            Utils.debug_and_log_data(aux_data.debug, aux_data.logger, f'Operation: {opt}')
            if opt == '+':
                subtechniques_available = Utils.get_subtechniques(family, steps_info, "--", special_tech)
                add_subtechnique = random.choice(subtechniques_available)
                pos = random.randint(1, len(subtechniques_cleaned) - 1)
                subtechniques_cleaned = subtechniques_cleaned[:pos] + [add_subtechnique] + subtechniques_cleaned[pos:]
                Utils.debug_and_log_data(aux_data.debug, aux_data.logger, f'{add_subtechnique} is going to be added to position {pos}. Updated action: {subtechniques_cleaned}')
            elif opt == '-':
                if len(subtechniques_cleaned) > 2:
                    pos = random.randint(1, len(subtechniques_cleaned) - 2)
                    subtechniques_cleaned = subtechniques_cleaned[:pos] + subtechniques_cleaned[pos + 1:]
                    Utils.debug_and_log_data(aux_data.debug, aux_data.logger, f'Position to remove sub: {pos}')
                else:
                    operation_added = np.random.choice(aux_data.action_operations, p = [0.7, 0.1, 0.1, 0.1])
                    operations.append(operation_added)
                    Utils.debug_and_log_data(aux_data.debug, aux_data.logger, f'Cannot remove open and close steps! The operation {operation_added} was added')       
                Utils.debug_and_log_data(aux_data.debug, aux_data.logger, f'Updated action: {subtechniques_cleaned}')
            elif opt == '%':
                if len(subtechniques_cleaned) > 2:
                    pos = random.randint(1, len(subtechniques_cleaned) - 2)    
                    subtechniques_available = Utils.get_subtechniques(family, steps_info, subtechniques_cleaned[pos], special_tech)
                    to_update_subtechnique = random.choice(subtechniques_available)
                    subtechniques_cleaned = subtechniques_cleaned[:pos] + [to_update_subtechnique] + subtechniques_cleaned[pos+1:]
                    Utils.debug_and_log_data(aux_data.debug, aux_data.logger, f'The step in position {pos} was changed with {to_update_subtechnique}. Updated action: {subtechniques_cleaned}')    
                else:
                    operation_added = np.random.choice(aux_data.action_operations, p=[0.7, 0.1, 0.1, 0.1])
                    operations.append(operation_added)
                    Utils.debug_and_log_data(aux_data.debug, aux_data.logger, f'Cannot change since only open and close steps! The operation {operation_added} was added')    
            else:
                Utils.debug_and_log_data(aux_data.debug, aux_data.logger, f'No changes to the action since the operation is: {opt}')    
            
        Utils.debug_and_log_data(aux_data.debug, aux_data.logger, f'Analyst action after transformations: {subtechniques_cleaned}') 
        return subtechniques_cleaned
    
    # Gets the duration of an action with outlier
    def get_action_duration_outlier(action_dur, outlier, outlier_cost):
        
        if outlier:
            action_outlier = action_dur + round(action_dur * outlier_cost, 1)
            #print("Action duration with outlier:", action_outlier)
        else:
            action_outlier = action_dur 
            
        return action_outlier
    
    # Converts the action format
    def change_action_format(action):
        
        if "[" in action:
            action_updated = ast.literal_eval(action)
            return action_updated
        else:
            if not isinstance(action, list):
                action = action.replace("''", ",")
                action = action.replace("'", "")
                action_divided = action.split(",")
                action_updated = [str(x) for x in action_divided]
                return action_updated
            return action
        
    # Gets the analyst growth
    def get_speed(curve, x):
        return round((-math.log(x*curve, 10)+2)/2, 2)
    
    # Updates the speed of a step
    def update_step_speed(steps_data, step, analyst_growth, improvement_type):
        
        learning_rate = steps_data[step]["learning_rate"]
        #print("Curr learning rate:", learning_rate)
        if improvement_type == "improve":
            learning_rate += 0.001
        else:
            learning_rate -= 0.001
        learning_rate = round(learning_rate, 3)
        speed_updated = Utils.get_speed(analyst_growth, learning_rate)
        return learning_rate, speed_updated
    
    # Get the next teams
    def get_remaining_teams(curr_team, all_teams):
        
        remaining_teams = []
        
        if curr_team in all_teams:
            for team_idx in range(all_teams.index(curr_team) + 1, len(all_teams)):
                next_team = all_teams[team_idx]
                remaining_teams.append(next_team)
            
        return remaining_teams
    
    # Verifies if a dictionary is sorted by datetime
    def is_dict_sorted(my_dict):
        values = list(my_dict.values())
        for i in range(len(values) - 1):
            current_datetime = values[i]['raised']
            next_datetime = values[i + 1]['raised']
            if current_datetime > next_datetime:
                return False
        return True
    
    # Verifies if all teams have treated the tickets
    def check_teams_tickets(all_tickets):
        
        for team in all_tickets:
            if bool(all_tickets[team]):
                return True
                
        return False
    
    # Gets the next ticket treated from different teams
    def get_next_ticket_different_teams(all_tickets):
        
        min_raised_tsp, ticket, team_picked, key_picked = None, None, None, None
        
        for team in all_tickets:
            #print("Check team:", team)
            if bool(all_tickets[team]):
                first_key = list(all_tickets[team].keys())[0]
                #print("First key:", first_key)
                first_ticket = all_tickets[team][first_key]
                if min_raised_tsp == None:
                    key_picked = first_key
                    ticket = first_ticket
                    min_raised_tsp = first_ticket["raised_tsp"]
                    team_picked = team
                else:
                    if min_raised_tsp > first_ticket["raised_tsp"]:
                        #print("Picked")
                        key_picked = first_key
                        ticket = first_ticket
                        min_raised_tsp = first_ticket["raised_tsp"]
                        team_picked = team
               
        return key_picked, ticket, team_picked
    
    # Gets the upper teams compared to a current one
    def get_next_teams(team, all_teams):
    
        next_teams = []
        #print("All teams:", all_teams)
        if team in all_teams:
            curr_team_idx = all_teams.index(team)
            for next_team_idx in range(curr_team_idx, len(all_teams)):
                next_teams.append(all_teams[next_team_idx])
    
        #print("Next_teams:", next_teams)
        return next_teams
    
    # Updates ticket id to include replicated tickets
    def get_increment_with_id_greater(curr_id, replicated_ids):
        
        increment = 0
        for element in replicated_ids:
            if element < curr_id:
                increment += 1
        #print("Increment:", increment)
        return increment
    
    # Calculates the Levenshtein distance between two lists
    def calculate_with_levenshtein(a,b):
        
        n, m = len(a), len(b)
        if n > m:
            a,b = b,a
            n,m = m,n
        
        current = range(n+1)
        for i in range(1,m+1):
            previous, current = current, [i]+[0]*n
            for j in range(1,n+1):
                add, delete = previous[j]+1, current[j-1]+1
                change = previous[j-1]
                if a[j-1] != b[i-1]:
                    change = change + 1
                current[j] = min(add, delete, change)
            
        return current[n]
    
    # Calculates similarity between picked action and subfamily action
    def calculate_distance(action_chosen, subfamily_action):
  
        subfam_action = subfamily_action.split("'")
        subfam_action = [x for x in subfam_action if x]
        
        distance = Utils.calculate_with_levenshtein(action_chosen, subfam_action)
        #print("Distance", distance)
        
        return distance
    
    # Gets the most recent generation id
    def get_most_recent_generation_id(path):
        
        matching_files = []
        gen_id = None
        substring = "trainDataset_"
        for filename in os.listdir(path):
            if substring in filename:
                matching_files.append(filename)
                
        #print("Matching files:", matching_files)
        if matching_files:
            # Sort the matching_files list based on the modification time in descending order
            sorted_files = sorted(matching_files, key=lambda x: os.path.getmtime(os.path.join(path, x)), reverse=True)
            last_modified_file = sorted_files[0]
            #print("Last modified file:", last_modified_file)
            
# =============================================================================
#             match = re.search(r'_(.*?)_', last_modified_file)
#             if match:
#                 gen_id = match.group(1)
#             else:
#                 gen_id = None
# =============================================================================
            if ".csv" in last_modified_file:
                gen_id = Utils.replace_before_and_after(last_modified_file, substring, ".csv")
            else:
                gen_id = Utils.replace_before_and_after(last_modified_file, substring, ".xlsx")
            #print(f"Last modified file with substring '{substring}': {gen_id}")

        return gen_id
    
    # Processes and optimizes the data of dataframe
    def process_dataset(data, train):

        # Categories columns may reduce the memory usage but slows groupby operations
        data['id'] = data['id'].astype('int32')
        #data['priority'] = data['priority'].astype('int8')
        data['raised'] = pd.to_datetime(data['raised'], infer_datetime_format=True)
        data['allocated'] = pd.to_datetime(data['allocated'], infer_datetime_format=True)
        data['action'] = data['action'].astype('str')
        
        categorical_columns = ['country', 'client', 'family', 'subfamily', 'init_priority', 'priority']
        for col in categorical_columns:
            data[col] = data[col].astype('category')
            
        row_names = Utils.filter_string(list(data.columns), ["feature"])
        #print("Row_names_", row_names)
        for col in row_names:
            data[col] = data[col].astype('bool')
            
        ip_data = ["destination_ip", "destination_port", "source_ip", "source_port"]
        for col in ip_data:
            if col in data.columns: 
                data[col] = data[col].astype('str')

        if train:
            data['stages'] = data['stages'].astype('str')
            data['similar'] = data['similar'].astype('str')
            data['fixed'] = pd.to_datetime(data['fixed'], infer_datetime_format=True)
            categorical_columns = ['family action', 'subfamily action', 'team', 'analyst', 'status', 'action status']
            for col in categorical_columns:
                data[col] = data[col].astype('category')
                
            data = data.drop(columns=["inheritance elapsed time", "escalate", 'country', 'init_priority', 'subfamily action', 'wait time'])
        else:
            data['temp_allocated'] = data['allocated'] 
            data['temp_allocated_tsp'] = data['allocated_tsp'] 
        
        #print("Data columns:", data.dtypes)
      
        return data
    
    # Gets first n elements from a dictionary
    def get_first_n_elements(dictionary, n):
        return {key: dictionary[key] for key in list(dictionary)[:n]}
    
    # Creates a copy of a dictionary
    def copy_dict(copied_dict, original_dict):
        
        for key, value in original_dict.items():
            # Check if the attribute is a list
            if isinstance(value, (list, set)):
                # If it's a list, create a new list using list()
                copied_dict.update({key: set(value) if isinstance(value, set) else list(value)})
            elif isinstance(value, dict):
                copied_dict[key] = {}
                Utils.copy_dict(copied_dict[key], value)
            else:
                # If it's not a list, just update the value
                copied_dict.update({key: value})
                
    # Instantiates a new family
    def instantiate_family(alert_pool, family, subfamilies_number, max_features, distribution_data, aux_data, ip):
        
        weekday_shifts, weekend_shifts, weekday_probs, time_daylight_shifts, time_night_shifts, time_light_probs, family_time_shifts_probs, family_week_shifts_probs = Utils.get_shift_data(distribution_data)
        
        alert_pool[family] = {}
        alert_pool[family]["subtypes"] = subfamilies_number
        alert_pool[family]["priority"] = random.randint(1, aux_data.priority_levels)
        
        #print("Time probs", distribution_data.time_equal_probabilities)
        if not distribution_data.time_equal_probabilities:
            timehour = np.random.choice([True, False], p=[time_light_probs, float(1 - time_light_probs)])

            if timehour:
                time_shift = random.choice(time_daylight_shifts)
            else:          
                time_shift = random.choice(time_night_shifts)
        else:
            time_shift = np.random.choice(list(distribution_data.family_time_4h.keys()), p = family_time_shifts_probs)
              
        if distribution_data.distribution_mode == "normal":
            alert_pool[family]["time shift"] = time_shift
            alert_pool[family]["time dev"] = 3
            
            if not distribution_data.week_equal_probabilities:
                weekday = np.random.choice([True, False], p=[weekday_probs, float(1 - weekday_probs)])
                if weekday:
                    week_shift = random.choice(weekday_shifts)
                else:          
                    week_shift = random.choice(weekend_shifts)
            else:
                week_shift = np.random.choice(list(distribution_data.week_time.keys()), p = family_week_shifts_probs)  

            alert_pool[family]["week shift"] = week_shift
            alert_pool[family]["week loc"] = week_shift
            alert_pool[family]["week dev"] = 1
                    
            shift_time = distribution_data.family_time_4h[time_shift]
            shift_time_init = shift_time['start']
            shift_time_init = shift_time_init.replace(".00", "")
            shift_time_end = shift_time['end']
            shift_time_end = shift_time_end.replace(".00", "")
                            
            hours_init, minutes_init, seconds_init = map(int, shift_time_init.split(':'))
            hours_end, minutes_end, seconds_init = map(int, shift_time_end.split(':'))
                    
            x = random.uniform(hours_init, hours_end + (minutes_end/60))

            temp = str(x).split('.')
            loc = float(f'{temp[0]}.{temp[1]}')
            alert_pool[family]['time loc'] = loc
                            
            Utils.debug_and_log_data(aux_data.debug, aux_data.logger, f'Shift Time init: {shift_time_init}, Shift Time end: {shift_time_end}, Hour start: {hours_init}, Hour end: {hours_end + (minutes_end/60)}, Time loc: {alert_pool[family]["time loc"]}, Week loc: {alert_pool[family]["week loc"]}')
                
        alert_pool[family]["extra_features"] = []
        n_extra_features = random.randint(0, max_features)
        selected_features = random.sample(range(max_features), n_extra_features)
        #print("Selected features:", selected_features)

        for i in selected_features:
            feature_id = f'_feature_{i}'
            alert_pool[family]["extra_features"].append(feature_id)
           
        if ip:
            alert_pool[family]["ip"] = np.random.choice([True, False], p=[0.3, 0.7])
            #if alert_pool[family]["ip"]:
            #    print("Has Ip")
            
    # Assigns the probability of a family occuring according to their week and time probabilities
    def assign_family_probabilities(family, alert_pool, n_time_slots, distribution_data):

        distribution_data.family_week_probability_pool[family], distribution_data.family_time_probability_pool[family] = {}, {}
        normal_dist = False

        if "time loc" in alert_pool[family]:
            #print(f'Family {family} follows a normal distribution.')
            normal_dist = True
            week_loc = alert_pool[family]['week loc']
            week_dev = alert_pool[family]['week dev']
            time_loc = alert_pool[family]['time loc']
            time_dev = alert_pool[family]['time dev']
        #else:
            #print(f'Family {family} follows a uniform distribution.')
        
        for day_shift in distribution_data.week_time.keys():
            if normal_dist:
                prob_day = NormalDist(mu = week_loc, sigma = week_dev).pdf(day_shift)
                prob_before_day = NormalDist(mu = week_loc, sigma = week_dev).pdf(day_shift - 7)
                prob_after_day = NormalDist(mu = week_loc, sigma = week_dev).pdf(day_shift + 7)
                distribution_data.family_week_probability_pool[family][distribution_data.week_time[day_shift]['day']] =  prob_day + prob_before_day + prob_after_day 
            else:
                distribution_data.family_week_probability_pool[family][distribution_data.week_time[day_shift]['day']] =  random.uniform(0,1)
        
        minute = 5
        hour = 0
            
        for slots in range(int(n_time_slots)):
            if hour == 24:
                time_string = "23:59"
                hour = 23
                minute = 59
            else:
                curr_time = time(hour, minute)    
                time_string = curr_time.strftime('%H:%M')             
        
            if normal_dist:
                temp_time = float(hour + (minute/60))
                prob_time = NormalDist(mu = time_loc, sigma = time_dev).pdf(temp_time)
            
                temp_before_time = float(hour + (minute/60)) - 24   
                prob_before_time = NormalDist(mu = time_loc, sigma = time_dev).pdf(temp_before_time)

                temp_after_time = float(hour + (minute/60)) + 24
                prob_after_day = NormalDist(mu = time_loc, sigma = time_dev).pdf(temp_after_time)
            
                distribution_data.family_time_probability_pool[family][time_string] =  prob_time + prob_before_time + prob_after_day 
            else:      
                distribution_data.family_time_probability_pool[family][time_string] =  random.uniform(0,1)

            minute = minute + 5
            if minute == 60:
                minute = 0
                hour = hour + 1 
                
    # Splits the techniques duration according to its size
    def split_steps_dur(x, n_techniques):
        
        durations = []
        #total_sum = x * len(techniques)
        #print("The total sum must be:", total_sum)
        
        #print("N_technqiues", n_techniques)
        i = 0
        if n_techniques == 1:
            durations.append(x)
        else:
            while i < n_techniques:
                durations.append(int(random.normalvariate(x, 1)))
                i+= 1
                #print("I:", i)
            
        #print("Duration:", durations)
        return durations
    
    # Divides the tickets for all teams
    def split_subfamilies_for_each_team(subfamilies_pool, prioritize_lower_teams, teams_frequency):
        
        teams = {}
        tickets_copy = (list(subfamilies_pool.keys())).copy()
        random.shuffle(tickets_copy)
        
        #print("Prioritize Lower teams", prioritize_lower_teams)
        if not prioritize_lower_teams: 
            # Convert percentages to float
            for i in teams_frequency.keys():
                if isinstance(teams_frequency[i], int):
                    teams_frequency[i] = teams_frequency[i]/100

            l1_percentage = teams_frequency['L1']
            l2_percentage = l1_percentage + teams_frequency['L2']
            l3_percentage = l2_percentage + teams_frequency['L3']
            #l4_percentage = teams_frequency['L1'] + teams_frequency['L2'] + teams_frequency['L3'] + ['L1']

            teams["L1"], teams["L2"], teams["L3"], teams["L4"] = np.split(tickets_copy, [int(len(tickets_copy)*l1_percentage), int(len(tickets_copy)*l2_percentage), int(len(tickets_copy)*l3_percentage)])
            #print("Teams", teams)
        
            for team in teams.keys():
                for subfamily in teams[team]:
                    subfamilies_pool[subfamily]["assigned team"] = team
        else:
            for subfamily in tickets_copy:
                subfamilies_pool[subfamily]["assigned team"] = "L1"
                
    # Build subfamily action
    def build_subfamily_action(team, family, subfamily, action, family_steps_pool, aux_data):

        Utils.debug_and_log_data(aux_data.debug, aux_data.logger, f'Team: {team}, family: {family}, subfamily: {subfamily}, family action: {action}')
    
        updated_action = ""
        for i in range(len(action)):
            ch = action[i]
            if ch in family_steps_pool[team][family].keys() and family_steps_pool[team][family][ch] != None:
                transformations = list(family_steps_pool[team][family][ch].keys())
                new_ch = "'" + str(random.choice(transformations)) + "'"
                Utils.debug_and_log_data(aux_data.debug, aux_data.logger, f'Step {ch} can be replace by {list(transformations)}. Step {ch} will be replaced by {new_ch}')
                updated_action = f'{updated_action}{new_ch}'
            else:
                updated_action = f'{updated_action}{ch}'
                
        Utils.debug_and_log_data(aux_data.debug, aux_data.logger, f'After converting: {updated_action}')

        #self.subfamily_pool[subfamily]["action"] = updated_action 
        return updated_action 
                
    # Builds actions for each team on a particular subfamily
    def build_subfamily_action_teams(teams_data, family, subfamily, family_actions, family_steps_pool, subfamily_pool, aux_data):
        
        for curr_team in teams_data.keys():
            sub_action = Utils.build_subfamily_action(curr_team, family, subfamily, family_actions[family]["action"], family_steps_pool, aux_data)
            subfamily_pool[subfamily]['teams_actions'][curr_team] = sub_action 
            Utils.debug_and_log_data(aux_data.debug, aux_data.logger, f'Curr team: {curr_team} - Sub action: {sub_action}')
            
    # Updates the duration of a step from the transition steps
    def update_step_outlier(transitions_dur, outlier_cost):
            
        transitions_dur_updated = []
        
        for i in transitions_dur:
            dur_updated = i + outlier_cost * i
            transitions_dur_updated.append(dur_updated)
            
        return transitions_dur_updated
    
    # Gets the extra features used by a family
    def get_extra_features_used(family_pool):
        
        extra_feat = {}
        for fam in family_pool:
            if family_pool[fam]["ip"]:        
                extra_feat["source_ip"], extra_feat["source_port"], extra_feat["destination_ip"], extra_feat["destination_port"] = [],[],[],[]
            for feature in family_pool[fam]["extra_features"]:    
                if feature not in extra_feat:
                    extra_feat[feature] = []
        
        extra_feat = dict(sorted(extra_feat.items()))
        #print("Extra features:", extra_feat)
        return extra_feat
    
    # Applies special format to the output file
    def format_generation_datasets(data, name, format_idx, dataset_params, extra_feat):

        extra_feat = {k: v for k,v in extra_feat.items() if v}
        #print("extra:", extra_feat)
        for i in extra_feat:
            data[i] = extra_feat[i]
            data_columns = data.keys()
        
        #print("Data columns:", data_columns)
        if "trainDataset" in name:
            params = [k for k, v in dataset_params.items() if v == False]
            #print("Params:", params)
            for item_name in params:
                #print("Item name:", item_name)
                items_columns = [item for item in data_columns if item_name in item]
                #print("Columns:", items_columns)
                for column in items_columns:
                    del data[column]

        dataset = pd.DataFrame(data, columns=list(data.keys()))
        dataset['id'] = dataset['id'].astype('int64')
        dataset['priority'] = dataset['priority'].astype('int8')
        dataset['init_priority'] = dataset['init_priority'].astype('int8')
        
        categorical_columns = ['country', 'client', 'family', 'family', 'subfamily', 'team', 'analyst', 'status']
        for col in categorical_columns:
            dataset[col] = dataset[col].astype('category')

        if "trainDataset" in name:    
            dataset['duration'] = dataset['duration'].astype('float32')
            dataset['duration_outlier'] = dataset['duration_outlier'].astype('float32')
            categorical_columns = ['family action', 'subfamily action', 'action status'] #'inheritance elapsed time']
            for col in categorical_columns:
                dataset[col] = dataset[col].astype('category')
    
        #print(dataset.columns)
        if format_idx == 0:
            filename = f'./Output/Generation/{name}.csv'
            dataset.to_csv(filename, encoding='utf-8', index=False, sep=';')
        else:
            if not Utils.check_excel_limit_rows(dataset, name): 
                filename = f'./Output/Generation/{name}.xlsx'
                writer = pd.ExcelWriter(filename, engine='xlsxwriter')
                dataset.to_excel(writer, sheet_name='Tickets Info', index = False)  
                workbook  = writer.book
                #worksheet = writer.sheets['Tickets Info']   
                
                # Add special format for better reading and debug
                format1 = workbook.add_format()
                format1.set_align('center')
    
                #worksheet.set_column(dataset.columns.get_loc("ID"), dataset.columns.get_loc("Time Difference"), 7, format1)
                #worksheet.set_column(dataset.columns.get_loc("Location"), dataset.columns.get_loc("Time Difference"), 18, format1, {'level': 1, 'hidden': True})
                #worksheet.set_column(dataset.columns.get_loc("Ticket Raised (UTC)"), dataset.columns.get_loc("Users Off Days"), 20, format1)
                #worksheet.set_column(dataset.columns.get_loc("Team Users"), dataset.columns.get_loc("Users Next Shift"), 20, format1, {'level': 1, 'hidden': True})
                #worksheet.set_column(dataset.columns.get_loc("Users Available"), dataset.columns.get_loc("Destination PORT"), 20, format1)
                
                writer.save()        
            #Utils.save_actions(dataset)
        return dataset
    
    # Checks if dataframe is sorted
    def check_dataframe_sorted(data):
        pd.set_option('display.max_rows', None)
        data['raised'] = pd.to_datetime(data['raised'])
        is_sorted = data['raised'].is_monotonic_increasing
        
        if not is_sorted:
            broken_positions = (data['raised']- data['raised'].shift(1)).dt.total_seconds() < 0
            print("Broken positions", data[broken_positions])
            
    # Plots the ticket distribution over the time
    def plot_dataset_distribution(ticket_dates):
        
        date_counts = Counter(ticket_dates)
        fig, ax = plt.subplots(figsize=(100, 20))
        ax.plot(list(date_counts.keys()), list(date_counts.values()), marker='o', linestyle='-', color='b')
        ax.set_xlabel('Date')
        ax.set_ylabel('Number of Tickets')
        ax.set_title("Dataset Generated Distribution")
        ax.yaxis.set_major_locator(plt.MaxNLocator(integer=True))
        plt.show()
        
    # Plots the wait time of the treating the tickets over time
    def plot_wait_times(tickets_duration, dates, title):
        
        fig, ax = plt.subplots(figsize=(80, 20))
        plt.ylim(0, max(tickets_duration))
        ax.plot(dates, tickets_duration, marker='o', linestyle='-')
        #ax.bar(dates, tickets_duration, width=0.2)
        ax.set_xlabel('Date', fontsize='large')
        ax.set_ylabel('Wait Time (Min)')
        ax.set_title(title, fontsize='x-large')
        plt.savefig(f'{title}.png', dpi=300, bbox_inches='tight')
        plt.show()
        
    # Plots the wait time of the treating the tickets over time in each priority level
    def plot_wait_times_by_init_priority(priorities_wait_time):
        
        for priority in priorities_wait_time:
            fig, ax = plt.subplots()
            #plt.ylim(0)
            ax.plot(list(priorities_wait_time[priority].keys()), list(priorities_wait_time[priority].values()), marker='o', linestyle='-', color='b')
            ax.set_xlabel('Date')
            ax.set_ylabel('Number of Tickets')
            ax.yaxis.set_major_locator(plt.MaxNLocator(integer=True))
            ax.set_title(f'Priority {priority}')
            plt.show()
            
    # Checks if is possible to use ticket seasonality with the datetime range selected
    def check_datetime_range_selected(start_date, end_date, ticket_seasonality_selector):
    
        if ticket_seasonality_selector:
            start_date_datetime = datetime.strptime(start_date, '%d-%m-%Y %H:%M:%S').strftime('%Y-%m-%d')
            end_date_datetime = datetime.strptime(end_date, '%d-%m-%Y %H:%M:%S').strftime('%Y-%m-%d')
            
            month_list = pd.date_range(start=start_date_datetime, end=end_date_datetime, freq='MS')
            month_list = [month.to_pydatetime().month for month in month_list]
            if len(month_list) < 12:
                print("Ticket seasonality was canceled because the dates selected don't cover the whole year!")
                return False
            else:
                return True
        return False
    
    # Gets the 5 minutes intervals probabilities of each family
    def get_time_slots(family_time_probability_pool):
        
        for fam in family_time_probability_pool:
            return list(family_time_probability_pool[fam].keys())
        
    # Calculates the probability of having more/less tickets (month and year) considering the growth rate and type
    def calculate_year_month_ticket_probabilities(growth_type, growth_rate, start_year, end_year):
        
        probabilities_dict, cumulative_dict= {}, {}
        cumulative_probability = 0
        
        if growth_type == "increase" or growth_type == "decrease":
            for year in range(start_year, end_year + 1):
                year_probs = []
                for month in range(1, 13):
                    total_months = (year - start_year) * 12 + month - 1
                    if growth_type == "increase":
                        probability = (1 + growth_rate) ** total_months
                    else:
                        probability = (1 - growth_rate) ** total_months
                    year_probs.append(probability)
                    cumulative_probability += probability
                probabilities_dict[year] = year_probs
            
            for year, month_probs in probabilities_dict.items():
                for i in range(12):
                    probabilities_dict[year][i] /= cumulative_probability

            #print("Year month probs:", probabilities_dict)
        
            cumulative_prob = 0
            for year, month_values in probabilities_dict.items():
                cumulative_dict[year] = []
                for i in range(len(month_values)):
                    cumulative_prob += month_values[i]
                    cumulative_dict[year].append(cumulative_prob)
                
            #print("Cumulative year month probs", cumulative_dict)
            return probabilities_dict, cumulative_dict
        else:
            return None, None
        
    # Generates a random date between stime and etime
    def generate_date(stime, etime):
        
        ptime = stime + random.random() * (etime - stime)
        timestamp = calendar.timegm(pytz.utc.localize(datetime.utcfromtimestamp(ptime)).utctimetuple())
        date = datetime.utcfromtimestamp(timestamp).replace(tzinfo=pytz.utc)
        #print("Date:", date)
        
        return date, timestamp
    
    # Validates the generated date considering the year, weekday and time of the day (defined a priori by the user)
    def validate_date(stime, etime, weekday_prob, time_light_probs, year_probs):
        
        date, timestamp = Utils.generate_date(stime, etime)
        
        random_time_prob = random.random()
        random_week_prob = random.random()   
        
        while year_probs != None or time_light_probs != None or weekday_prob != None:
            year_picked, month_picked = None, None
            found = False
            random_year_prob = random.random()
            
            if year_probs != None:
                for year in year_probs.keys():
                    for month_value in year_probs[year]:
                        if random_year_prob < month_value:
                            year_picked = year
                            month_picked = year_probs[year].index(month_value) + 1
                            found = True
                            break
                    if found:
                        break
                    
            if time_light_probs != None:
                while True:   
                    if date.hour >= 8 and date.hour <= 20: 
                        if random_time_prob < time_light_probs:
                            break
                    else:  # Weekend
                        if random_time_prob >= time_light_probs:
                            break 
                    date, timestamp = Utils.generate_date(stime, etime) 
        
            if weekday_prob != None:
                while True:   
                    if date.weekday() < 5: 
                        if random_week_prob < weekday_prob:
                            break
                    else:  # Weekend
                        if random_week_prob >= weekday_prob:
                            break
                    date, timestamp = Utils.generate_date(stime, etime)
                    continue
        
            if year_probs != None:
                if date.year == year_picked and date.month == month_picked:
                    break
                    
                date, timestamp = Utils.generate_date(stime, etime)
                #print("Resume time analysis after year failed")
        
        return timestamp, date
    
    # Generates a random date in a certain place
    def get_country_data(country, stime, etime, debug, ticket_seasonality_selector, ticket_seasonality_season, weekday_prob, time_light_probs, probabilities_dict, aux_data):  

        new_timestamp, new_date = Utils.validate_date(stime, etime, weekday_prob, time_light_probs, probabilities_dict)

        Utils.debug_and_log_data(aux_data.debug, aux_data.logger, f'Timestamp generated on {new_date} on {country}')

        if ticket_seasonality_selector:
            months_available = ticket_seasonality_season["months"]
            #print("Months available:", months_available)
        
            while new_date.month not in months_available or new_timestamp > etime or new_timestamp < stime:
                Utils.debug_and_log_data(aux_data.debug, aux_data.logger, f'Date rejected {new_date}')
                new_timestamp, new_date = Utils.validate_date(stime, etime, weekday_prob, time_light_probs, probabilities_dict)
        else:
            while new_timestamp > etime or new_timestamp < stime:
                Utils.debug_and_log_data(aux_data.debug, aux_data.logger, f'Date rejected {new_date}')
                new_timestamp, new_date = Utils.validate_date(stime, etime, weekday_prob, time_light_probs, probabilities_dict)

        return new_timestamp, new_date
    
    # Generates a random location (country)
    def get_country_network(networks, networks_used, aux_data):

        random_network = random.choice(networks)
        Utils.debug_and_log_data(aux_data.debug, aux_data.logger, "Country of each ticket assigned")
        #print("Network chosen", random_network)
    
        return random_network
    
    # Gets the family and subfamily of of the ticket according to its time and weekday
    def get_family_subfamily(alert_pool, sub_alert_pool, distribution_data, ticket, suspicious_data, aux_data, ip, new_family, new_subfamily, time_slots, families_used, ticket_type):

        ticket_time = '{:02d}:{:02d}'.format(ticket['raised'].hour, ticket['raised'].minute)
        curr_time_slot = Utils.get_current_time_slot(time_slots, ticket_time)        

        if not new_family:
            day = calendar.day_name[ticket['raised'].weekday()]
            month = calendar.month_name[ticket['raised'].month]
            family = ""
            ticket_time_probs, ticket_week_probs, ticket_family_probs, family_cumulative = {}, {}, {}, {}

            for k in distribution_data.family_time_probability_pool.keys():
                ticket_time_probs[k] = distribution_data.family_time_probability_pool[k][curr_time_slot]

            for q in distribution_data.family_week_probability_pool.keys():
                ticket_week_probs[q] = distribution_data.family_week_probability_pool[q][day]
                
            if distribution_data.family_seasonality_selector:
                for k in alert_pool.keys():
                    month_ticket_sazonality = distribution_data.family_seasonality[month]
                    ticket_family_probs[k] = month_ticket_sazonality[alert_pool[k]["real_family"]]
                        
            ticket_probs_total = {x: ticket_time_probs.get(x) * ticket_week_probs.get(x) for x in ticket_time_probs}
              
            if distribution_data.family_seasonality_selector:
                ticket_probs_total = {x: ticket_probs_total.get(x) * ticket_family_probs.get(x) for x in ticket_probs_total}

            ticket_probs_sorted = sorted(ticket_probs_total.items(),  key=itemgetter(1))
            
            ticket_random = random.uniform(0,  sum(ticket_probs_total.values()))
            Utils.debug_and_log_data(aux_data.debug, aux_data.logger, f'Family time options: {ticket_time_probs}\nFamily week options: {ticket_week_probs}\nFamily time options sorted: {ticket_probs_sorted}, Random prob: {ticket_random}')
        
            prev = 0
            for l in range(0, len(ticket_probs_sorted)):
                fam = ticket_probs_sorted[l][0]
                if l == 0:
                    prev = ticket_probs_sorted[0][1]
                    family_cumulative[fam] = prev
                else:
                    prev = prev + ticket_probs_sorted[l][1]
                    family_cumulative[fam] = prev 
                    
            Utils.debug_and_log_data(aux_data.debug, aux_data.logger, f'Family cumulative: {family_cumulative}')
            for t in family_cumulative.keys():
                if ticket_random < family_cumulative[t]:
                    family = t
                    break
                
            subfamily = random.randint(1, alert_pool[family]["subtypes"])  
            if ticket_type == "test":
                if family not in families_used["train"]:
                    Utils.debug_and_log_data(aux_data.debug, aux_data.logger, f'Family doesnt exist in training data. New family: {family}')
                    #print("ticket time:", ticket["raised"])
                    ticket["new_family"] = True
                else:
                    if new_subfamily:
                        ticket["new_subfamily"] = True
                        Utils.debug_and_log_data(aux_data.debug, aux_data.logger, f'SubFamily doesnt exist in training data. SubFamilies used {families_used}')

                        if len(families_used["train"][family]) >= alert_pool[family]["subtypes"]:
                            if family in families_used["test"]:
                                subfamily = len(families_used["train"][family]) + len(families_used["test"][family])
                            else:
                                subfamily = len(families_used["train"][family]) + 1
                            print("New subfamily generated after maxing the subtypes originally set")
                        else:
                            all_subtypes = list(range(1, alert_pool[family]["subtypes"] + 1))
                            set1 = set(all_subtypes)
                            set2 = set(families_used["train"][family])
                            available_subfamilies = list(set1 - set2)
                            subfamily = random.choice(available_subfamilies)
                            print("New subfamily generated using the subtypes originally set")
                    else:   
                        subfamily = random.choice(families_used["train"][family])  

            subfamily_updated = f'{family}_{subfamily}'  
            Utils.debug_and_log_data(aux_data.debug, aux_data.logger, f'Subfamily updated: {subfamily_updated}')
        else:
            ticket["new_family"] = True
            family_features_used = []
            
            family = Utils.generate_new_family(list(alert_pool.keys()))
            
            for fam in alert_pool:
                n_features = len(alert_pool[fam]["extra_features"])
                if n_features not in family_features_used:
                    family_features_used.append(n_features)
                    
            new_family_features = random.choice([i for i in range(max(family_features_used) + 1, max(family_features_used) + 2) if i not in family_features_used])
            
            Utils.instantiate_family(alert_pool, family, 1, new_family_features, distribution_data, aux_data, ip)
            n_time_slots = (60/5) * 24 
            Utils.assign_family_probabilities(family, alert_pool, n_time_slots, distribution_data)
                
            subfamily = alert_pool[family]["subtypes"]
            subfamily_updated = f'{family}_{subfamily}'
            #print("New subfamily created:", subfamily_updated)

        if subfamily_updated not in sub_alert_pool:
            sub_alert_pool[subfamily_updated] = {}
            sub_alert_pool[subfamily_updated]['teams_actions'] = {}

            sub_alert_pool[subfamily_updated]['suspicious'] = np.random.choice([True, False], p=[suspicious_data.suspicious_subfamily, 1 - suspicious_data.suspicious_subfamily])
            sub_alert_pool[subfamily_updated]['max_counter'] = random.randint(suspicious_data.min_coordinated_attack, suspicious_data.max_coordinated_attack)
            sub_alert_pool[subfamily_updated]['timerange'] = random.randint(suspicious_data.min_coordinated_attack_minutes, suspicious_data.max_coordinated_attack_minutes)
        
        ticket['family'] = family
        ticket['subfamily'] = subfamily_updated
        
        if family not in families_used[ticket_type]:
            families_used[ticket_type][family] = []
            
        if subfamily not in families_used[ticket_type][family]:
            families_used[ticket_type][family].append(subfamily)
            
    # Verifies if a ticket is suspicious or not    
    def check_ticket_suspicious(ticket, suspicious, countries):
        if suspicious:
            country = ticket['country']
            if country in countries:
                start_ticket_time = datetime.strptime(countries[country]["widget start date"].text(), "%H:%M:%S.%f").time()
                end_ticket_time = datetime.strptime(countries[country]["widget end date"].text(), "%H:%M:%S.%f").time()
                if Utils.check_date_between(start_ticket_time, end_ticket_time, ticket['raised'].time()):
                    #print("Ticket id suspicious", ticket)
                    return True

        return False
    
    # Assigns the destination and source IP and port to a ticket
    def assign_ticket_ip(with_ip, ticket, clients_info, suspicious_ips, ips_pool, ip_selected_idx, countries, aux_data, dst_port_type):
        if with_ip:
            source_country = random.choice(list(countries.keys()))
            ticket['source_ip'], ticket['source_port'] = Utils.get_source_ip_port(source_country, ticket['suspicious'], countries, suspicious_ips, ips_pool, ip_selected_idx)
            ticket['destination_ip'], ticket['destination_port'] = Utils.get_destination_ip_port(clients_info[ticket["client"]][ticket["country"]]["networks"], aux_data, ips_pool, ip_selected_idx, dst_port_type)   
            
    # Sets the temporaries features  (e.g. "Feature_1) to 1 (existent)
    def set_extra_features_values(ticket, family_features):
        
        for f in family_features:
            if f not in ticket:
                ticket[f] = 1
                
    # Assesses the performance of the teams and their analysts in the different shifts
    def analyse_shifts_performance(shifts_data, teams_summary, team_analysts):
        
        total_n_tickets, total_time_spent, total_wait_time = 0,0,0
        for shift in shifts_data:
            total_n_tickets += shifts_data[shift]["n_tickets"]
            total_time_spent += shifts_data[shift]["time_spent"]
            total_wait_time += shifts_data[shift]["wait_time"]
            
        print("Total number of tickets treated by this team is", total_n_tickets)
        print("Average time spent (in minutes) by this team is", total_time_spent/total_n_tickets)
        print("Average wait time (in minutes) by this team is", total_wait_time/total_n_tickets)
        
        # Shift with the most tickets
        max_tickets_shift, max_tickets_count = Utils.get_max_min_in_dict(shifts_data, False, "n_tickets")
        print(f'The shift with more tickets fixed is shift {max_tickets_shift} with {max_tickets_count} tickets')
        # Shift with the least tickets
        min_tickets_shift, min_tickets_count = Utils.get_max_min_in_dict(shifts_data, True, "n_tickets")
        print(f'The shift with the least tickets fixed is shift {max_tickets_shift} with {min_tickets_count} tickets')
        # Shift with the most time spent
        max_time_spent_shift, max_time_spent = Utils.get_max_min_in_dict(shifts_data, False, "time_spent")
        print(f'The shift with more time spent is shift {max_time_spent_shift} with {max_time_spent} minutes')
        # Shift with the least time spent
        min_time_spent_shift, min_time_spent = Utils.get_max_min_in_dict(shifts_data, True, "time_spent")
        print(f'The shift with the least time spent is shift {min_time_spent_shift} with {min_time_spent} minutes')
        best_average_time_spent_shift = min(shifts_data, key=lambda shift: Utils.calculate_average_time(shifts_data[shift], "time_spent"))
        best_average_time_spent = Utils.calculate_average_time(shifts_data[best_average_time_spent_shift], "time_spent")
        print(f'The shift with the best average time spent is shift {best_average_time_spent_shift} with {best_average_time_spent} minutes')
        
        # Shift with the most wait time
        max_wait_time_shift, max_wait_time = Utils.get_max_min_in_dict(shifts_data, False, "wait_time")
        print(f'The shift with more wait time is shift {max_wait_time_shift} with {max_wait_time} minutes')
        # Shift with the least time spent
        min_wait_time_shift, min_wait_time = Utils.get_max_min_in_dict(shifts_data, True, "wait_time")
        print(f'The shift with more wait time is shift {min_wait_time_shift} with {min_wait_time} minutes')
        best_average_wait_time_shift = min(shifts_data, key=lambda shift: Utils.calculate_average_time(shifts_data[shift], "wait_time"))
        best_average_wait_time = Utils.calculate_average_time(shifts_data[best_average_wait_time_shift], "wait_time")
        print(f'The shift with the best average wait time is shift {best_average_wait_time_shift} with {best_average_wait_time} minutes')
        
        incidents_performance = {}
        for shift in teams_summary.keys():
            #print("Current shift:", shift)
            analysts_performance = {}

            for ticket_id in teams_summary[shift].keys():
                curr_analyst = teams_summary[shift][ticket_id]["analyst"]
                if curr_analyst not in analysts_performance:
                    analysts_performance[curr_analyst] = {}
                    analysts_performance[curr_analyst]["n_tickets"] = 0
                    analysts_performance[curr_analyst]["time_spent"] = 0
                analysts_performance[curr_analyst][ticket_id] = teams_summary[shift][ticket_id]["time_spent"]
                analysts_performance[curr_analyst]["n_tickets"] += 1
                analysts_performance[curr_analyst]["time_spent"] += teams_summary[shift][ticket_id]["time_spent"]
                
                curr_family = teams_summary[shift][ticket_id]["family"]
                curr_subfamily = teams_summary[shift][ticket_id]["subfamily"]
                Utils.get_incidents_treated_in_shift(curr_family, curr_subfamily, teams_summary[shift][ticket_id]["time_spent"], incidents_performance)

            # Analyst with more tickets fixed
            analyst_with_more_tickets_solved, max_tickets_solved = Utils.get_max_min_in_dict(analysts_performance, False, "n_tickets")
            print(f'The analyst from shift {shift} with more tickets fixed is {analyst_with_more_tickets_solved} with {max_tickets_solved}')
            # Analyst with less tickets fixed
            analyst_with_less_tickets_solved, min_tickets_solved = Utils.get_max_min_in_dict(analysts_performance, True, "n_tickets")
            print(f'The analyst from shift {shift} with less tickets fixed is {analyst_with_less_tickets_solved} with {min_tickets_solved}')
            # Analyst with more time spent
            analyst_with_more_time_spent, more_time_spent = Utils.get_max_min_in_dict(analysts_performance, False, "time_spent")
            print(f'The analyst from shift {shift} with more time spent is {analyst_with_more_time_spent} with {more_time_spent} minutes')
            # Analyst with more time spent
            analyst_with_less_time_spent, less_time_spent = Utils.get_max_min_in_dict(analysts_performance, True, "time_spent")
            print(f'The analyst from shift {shift} with more time spent is {analyst_with_less_time_spent} with {less_time_spent} minutes')
            best_average_time_spent_analyst = min(analysts_performance, key=lambda analyst: Utils.calculate_average_time(analysts_performance[analyst], "time_spent"))
            best_average_time_spent = Utils.calculate_average_time(analysts_performance[best_average_time_spent_analyst], "time_spent")
            print(f'The analyst with the best average time spent in shift {shift} is {best_average_time_spent_analyst} with {best_average_time_spent} minutes')
        
        family_average_time, subfamily_average_time = {}, {}
        for family, subfamilies in incidents_performance.items():
            family_total_time, family_total_tickets = 0, 0
            for subfamily, data in subfamilies.items():
                time_spent = data["time_spent"]
                n_tickets = data["n_tickets"]
                family_total_time += time_spent
                family_total_tickets += n_tickets
                subfamily_average_time[subfamily] = time_spent / n_tickets if n_tickets > 0 else 0

            family_average_time[family] = family_total_time / family_total_tickets if family_total_tickets > 0 else 0

        # Find family with the best and worst average time spent
        best_average_family = min(family_average_time, key=family_average_time.get)
        print(f'The family with the best average time spent is {best_average_family} with {family_average_time[best_average_family]} minutes')
        worst_average_family = max(family_average_time, key=family_average_time.get)
        print(f'The family with the worst average time spent is {worst_average_family} with {family_average_time[worst_average_family]} minutes')

        # Find subfamily with the best and worst average time spent
        best_average_subfamily = min(subfamily_average_time, key=subfamily_average_time.get)
        print(f'The subfamily with the best average time spent is {best_average_family} with {subfamily_average_time[best_average_subfamily]} minutes')
        worst_average_subfamily = max(subfamily_average_time, key=subfamily_average_time.get)
        print(f'The subfamily with the worst average time spent is {worst_average_subfamily} with {subfamily_average_time[worst_average_subfamily]} minutes')
        
    # Checks if dataset reach the max rows of Excel
    def check_excel_limit_rows(dataset, name):
        # Excel limit row is 1,048,576 
        if dataset.shape[0] > 104876:
            print("Saved on csv file due to excel limit rows!")
            filename = f'./Output/Generation/{name}.csv'
            dataset.to_csv(filename, encoding='utf-8', index=False, sep=';')
            #numpy_array = dataset.to_numpy()
# =============================================================================
#             np.savetxt(name, numpy_array, 
#                    header = header,
#                    delimiter=';', fmt='%s' , comments='')
# ============================================================================
            return True
        else:
            return False
        
    # Gets the time slot considering the current time
    def get_current_time_slot(time_slots, curr_time):
        
        # Binary search to find the first slot greater than or equal to the target time
        left, right = 0, len(time_slots) - 1
        found_slot = None

        while left <= right:
            mid = (left + right) // 2
            if time_slots[mid] >= curr_time:
                found_slot = time_slots[mid]
                right = mid - 1
            else:
                left = mid + 1

# =============================================================================
#         if found_slot is not None:
#             print(f"The first slot greater than or equal to {curr_time} is {found_slot}")
#         else:
#             print(f"No slot found greater than or equal to {curr_time}")
# =============================================================================
        
        return found_slot
    
    # Builds a new family incident
    def generate_new_family(all_families):
        
        new_family = random.choice(string.ascii_uppercase)
        letters = string.ascii_uppercase
        while new_family in all_families:
            print("Family already exists. Try another!")
            new_family_length = random.randint(1, 5)
            new_family = ''.join(random.choice(letters) for i in range(new_family_length))
            
        print("New Family:", new_family)
        return new_family
    
    # Generates the IP and Port of Source Country
    ## Port 0-1023 – Well known ports (server services by the Internet)
    ## Ports 1024-49151 - Registered Port (semi-served ports)
    ## Ports 49152-65535 - free to use by client programs (ephemeral ports)
    ## Source in the last
    ## Generates the Ports  
    def get_source_ip_port(country, suspicious, countries, suspicious_ips, ips_pool, ip_selected_idx):

        if not suspicious:
            ips_network_available = countries[country]["ips"]
            random_network = random.choice(ips_network_available)
            net = ipaddress.IPv4Network(random_network)
            random_ip_index = random.randint(0, net.num_addresses -1)
            random_ip = net[random_ip_index]
        else:
            random_ip = random.choice(list(suspicious_ips))

        #print("Source ip:", random_ip)
        src_port = random.randint(49152, 65535)    

        if ips_pool[ip_selected_idx] == "IPv6Address":
            random_ip = ipaddress.IPv6Address(f'2002::{random_ip}').compressed
            #print("Ip converted to IPv6")
            
        return random_ip, src_port

    # Generates the IP and Port of Destination Country
    def get_destination_ip_port(client_network, aux_data, ips_pool, ip_selected_idx, dst_port_type):

        random_network = random.choice(client_network)
        net = ipaddress.IPv4Network(random_network)

        random_ip_index = random.randint(0, net.num_addresses -1)
        random_ip = net[random_ip_index]
        
        Utils.debug_and_log_data(aux_data.debug, aux_data.logger, f'Network {net} has an range of {net.num_addresses}, Ip index: {random_ip_index}')
        
        if ips_pool[ip_selected_idx] == "IPv6Address":
            random_ip = ipaddress.IPv6Address(f'2002::{random_ip}').compressed
            #print("Ip converted to IPv6")
            
        dst_port_type = next(dst_port_type.generate())

        if dst_port_type == "well-known":
            dst_port = random.randint(0, 1023)
        else:
            dst_port = random.randint(1024, 49151)
        return random_ip, dst_port
    
    #Gets the subtechniques of each step of the family action
    def get_subtechniques(family, steps_pool, step, locked):
    
        subtechniques = []
        if isinstance(locked, dict):
            locked = Utils.flat_lists(list(locked.values()))

        family_techniques = steps_pool[family]
        #print("Family techniques", family_techniques)
        
        for i in family_techniques.keys():
            if i not in locked:
                for l in family_techniques[i].keys():
                    if l not in locked:
                        if step != l:
                            subtechniques.append(l)
        
        #print("Family subtechniques", subtechniques)
        return subtechniques
    
    # Gets the maximum/minimum value and key of a dictionary based on a particular feature
    def get_max_min_in_dict(data, is_min, feature):
        
        best_data_key, value = 0,0
        if not is_min:
            best_data_key = max(data, key=lambda data_key: data[data_key][feature])
            value = data[best_data_key][feature]
        else:
            best_data_key = min(data, key=lambda data_key: data[data_key][feature])
            value = data[best_data_key][feature]

        return best_data_key, value
    
    # Resets analyst's data
    def reset_analysts_data(generation_params, shifts, logger):
    
        analysts_info, shifts_picked, save_info, users_treated = {},{},{},{}
        existent_users = []

        for team in generation_params["analysts_skills"]:
            analysts_info[team], analysts_info[team]["analysts"] = {}, {}
            save_info[team], save_info[team]["analysts"] = {}, {}

            temp_team_users = list(generation_params["analysts_skills"][team]["analysts"].keys())
            if existent_users:
                temp_users =  list(set(temp_team_users) - set(existent_users))
                for i in temp_users:
                    temp_team_users.remove(i)
                
                team_shuffled = random.sample(temp_team_users, len(temp_team_users))
                team_shuffled = team_shuffled + temp_users
            else:
                team_shuffled = random.sample(temp_team_users, len(temp_team_users))
            
            Utils.debug_and_log_data(generation_params["debug"], logger, f'Team {team}. Members: {team_shuffled}')
            
            for member in team_shuffled:
                if member not in analysts_info[team]["analysts"].keys():
                    existent_users.append(member)
                    if member not in users_treated:
                        users_treated[member] = {}
                        shift_index = Utils.pick_shifts(shifts_picked, generation_params, shifts, logger)
                        users_treated[member]["shift"] = shift_index
                    else:
                        shift_index = users_treated[member]["shift"]
                        
                    if shift_index not in shifts_picked:
                        shifts_picked[shift_index] = 1
                    else:
                        shifts_picked[shift_index] += 1
                        
                    growth = round(random.uniform(1, 2), 2)
                    refusal_rate = round(random.uniform(0.1, 0.8), 2)
                    
                    start_date = datetime.utcfromtimestamp(0).replace(tzinfo=pytz.utc)
                    analysts_info[team]["analysts"][member], save_info[team]["analysts"][member] = {}, {}
                    Utils.update_data(analysts_info[team]["analysts"][member], shift = shift_index, growth = growth, refusal_rate = refusal_rate, assigned_ticket = None, fixed = start_date, fixed_tsp = 0, summary = {}, active = True)
                    Utils.update_data(save_info[team]["analysts"][member], shift = shift_index, growth = growth, refusal_rate = refusal_rate, active = True)
                    
                    Utils.debug_and_log_data(generation_params["debug"], logger, f'Shifts used: {shifts_picked}')
                else:
                    shifts_picked[analysts_info[team]["analysts"][member]["shift"]] += 1
                    Utils.debug_and_log_data(generation_params["debug"], logger, f'Analyst shift already assigned. Shifts used: {shifts_picked}')
        
            shifts_picked = {}
            
        Utils.debug_and_log_data(generation_params["debug"], logger, "All analysts shifts assigned")

        return analysts_info, save_info
    
    # Get the shift to be fill in by an operator
    def pick_shifts(shifts_used, generation_params, shifts_data, logger):
    
        shift_index = -1
        if generation_params["balanced_shifts"]:
            shifts_remaining = []
            for i in shifts_data.keys():
                if i not in shifts_used:
                    shifts_remaining.append(i)
                
            Utils.debug_and_log_data(generation_params["debug"], logger, f'Remaining Shifts: {shifts_remaining}')
            if not shifts_remaining:
                shift_index = min(shifts_used, key=shifts_used.get)
            else:
                shift_index = random.choice(shifts_remaining)
        else:
            shift_index = random.randint(0, len(shifts_data.keys())-1)
    
        Utils.debug_and_log_data(generation_params["debug"], logger, f'Shift index picked: {shift_index}')
        return shift_index
    
    # Get the probabilities of occuring during a weekday or weekend and during the day or night
    def get_shift_data(distribution_data):
        
        family_time_shifts_probs, family_week_shifts_probs = [], []
        family_time_shifts = distribution_data.family_time_4h.keys()
        family_week_shifts = distribution_data.week_time.keys()

        for i in family_time_shifts:
            family_time_shifts_probs.append(distribution_data.family_time_4h[i]['prob'])
            
        for l in family_week_shifts:
            family_week_shifts_probs.append(distribution_data.week_time[l]['prob'])

        weekday_shifts = [0, 1, 2, 3, 4]
        weekend_shifts = [5, 6]
        weekday_probs = family_week_shifts_probs[0] + family_week_shifts_probs[1] + family_week_shifts_probs[2] + family_week_shifts_probs[3] + family_week_shifts_probs[4]
        #weekend_probs = float (1 - weekday_probs)
        
        time_daylight_shifts = [2, 3, 4]
        time_night_shifts = [0, 1, 5]
        time_light_probs = family_time_shifts_probs[2] + family_time_shifts_probs[3] + family_time_shifts_probs[4]
        
        return weekday_shifts, weekend_shifts, weekday_probs, time_daylight_shifts, time_night_shifts, time_light_probs, family_time_shifts_probs, family_week_shifts_probs
    
    # Checks if a ticket should be escalated (initial escalation or max similarity)
    def check_escalated_similar_tickets(ticket_id, tickets_data, tickets_inheritance, ticket_similarity_selector, subfamily_pool, generation, aux_data):

        if tickets_data[ticket_id]["escalate"]:
            #tickets_data[ticket_id]["coordinated"] = "---"
            if tickets_data[ticket_id]["team"] != "L4":
                # print("Escalated")
                tickets_data[ticket_id]["replication_status"] = "Escalation"
                tickets_data[ticket_id]["status"] = "Transfer"
                Utils.debug_and_log_data(aux_data.debug, aux_data.logger, "To replicate due to escalation")
            else:
                Utils.debug_and_log_data(aux_data.debug, aux_data.logger, "Can't be replicated because it is already on the top team")
        else:
            if ticket_similarity_selector:
                if tickets_data[ticket_id]["replication_status"] == None:
                    Utils.check_similar_coordinated_tickets(tickets_data[ticket_id], tickets_data, tickets_inheritance, subfamily_pool, generation, aux_data)
                    
    # Stores the user input into a JSON file
    def save_input_data(output_path, generation_params, other_params):

        #print("Final:", generation_params["analysts_skills"])
        with open(output_path, 'w') as fd:
            fd.write(json.dumps([generation_params, other_params], indent=2, default=str)) 
        print("Input's info saved")