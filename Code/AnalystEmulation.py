from Code.Utils import Utils, BufferedRandomChoiceGenerator

import random#, sys, pytz
from datetime import datetime, timedelta

class AnalystEmulation:

    def __init__(self, gen_id, treatment_params, analysts_info, family_pool, subfamily_pool, family_steps_pool, special_steps, aux_data, seed):

        self._id = gen_id
        self.subfamily_analysts_action, self.subfamily_steps_speeds = {}, {}
        self.analyst_subfamily_action_probability = treatment_params["analyst_subfamily_action_probability"]
        self.analyst_same_action_probability = treatment_params["analyst_same_action_probability"]
        self.min_learning_counter = treatment_params["min_learning_counter"]
        self.max_learning_counter = treatment_params["max_learning_counter"]
        self.actions_similarity = treatment_params["actions_similarity"]
        self.shifts = treatment_params["shifts"]
        self.ticket_verification_selector = treatment_params["ticket_verification_selector"]
        self.ticket_similarity_selector = treatment_params["ticket_similarity_selector"]

        self.analysts_info = analysts_info
        self.family_pool = family_pool
        self.subfamily_pool = subfamily_pool
        self.family_steps_pool = family_steps_pool
        self.special_steps = special_steps
        self.seed = seed

        self.aux_data = aux_data
        self.priority_queues = {}

        for team in self.analysts_info:
            self.priority_queues[team] = {}
            Utils.instantiate_priority_queues(self.aux_data.priority_levels, self.priority_queues[team])

    # Updates the speed of each analyst-step
    def update_steps_duration(self, ticket):

        action = ticket["action"]
        steps_transitions = ticket["steps_transitions"]
        step_date = ticket["allocated_tsp"]
        team = ticket["team"]
        analyst = ticket["analyst"]
        subfamily = ticket["subfamily"]

        for step_idx in range(len(action)):
            step = action[step_idx]
            self.subfamily_steps_speeds[subfamily][team][analyst][step]["curr_counter"] += 1
            self.subfamily_steps_speeds[subfamily][team][analyst][step]["last_incident"] = step_date

            step_dur = steps_transitions[step_idx] * 60
            if ticket["outlier"]:
                step_dur += self.aux_data.outlier_cost * step_dur
            #print("Step dur:", step_dur)
            step_date += step_dur
        #print("Check analyst steps info:", self.subfamily_steps_speeds[team][subfamily][analyst])

    # Processes each ticket by allocating an analyst and action
    # @profile
    def process_tickets(self, thread_canceled, weight, tickets):

        Utils.log_data(self.aux_data.logger, "\nProcess tickets")
        
        initial_time = datetime.now()
        mode = 0
        tickets_inheritance, families_resolution = {}, {}
        locked_techniques = Utils.get_locked_techniques(self.special_steps)
        family_subtechniques = Utils.get_family_middle_subtechniques(self.family_steps_pool)
        
        Utils.set_seed(self.seed)
        
        #print(tickets)
        
        for team in self.priority_queues:
            if team in tickets:
                print(f'Analyse tickets in {team}')
                curr_id, original_dict_idx, n_replicated = 0, 0, 0
    
                tickets_updated = tickets[team]
                if team != "L1":
                    tickets_inheritance = {}

                #print("Number of tickets to treat:", len(tickets_updated))
                use_subfamily_action_choices = BufferedRandomChoiceGenerator([True, False], [self.analyst_subfamily_action_probability, 1 - self.analyst_subfamily_action_probability], 5000)
                use_same_action_choices = BufferedRandomChoiceGenerator([True, False], [self.analyst_same_action_probability, 1 - self.analyst_same_action_probability], 5000)

                curr_shift = Utils.get_ticket_shift(tickets_updated[curr_id]["allocated"].time())
                prev_shift = curr_shift
                #print("Curr shift:", curr_shift)
                analysts_in_shift = Utils.get_operators_in_shift(self.analysts_info[team], curr_shift)
                #print("Analysts_in_shift:", analysts_in_shift)
                original_keys = list(tickets_updated.keys())
        
                while curr_id != None:       
                    Utils.update_analysts_in_next_shift(self.analysts_info[team]["analysts"], team, tickets_updated[curr_id]["allocated"], prev_shift, curr_shift, self.analysts_info, None, self.shifts, self.aux_data.logger)
                    #print("Ticket id:", curr_id)                 
                    Utils.debug_and_log_data(self.aux_data.debug, self.aux_data.logger_active, self.aux_data.logger, f'Ticket id: {curr_id}, Allocated: {tickets_updated[curr_id]["allocated"]}, Priority: {tickets_updated[curr_id]["priority"]}')
                    
                    tickets_updated[curr_id]["replication_status"] = None
                    ticket_closed, close_shift = self.assign_analyst(curr_id, curr_shift, analysts_in_shift, tickets_updated, self.priority_queues, tickets_inheritance, locked_techniques, mode, True, use_subfamily_action_choices, use_same_action_choices, family_subtechniques)

                    if ticket_closed:                        
                        Utils.debug_and_log_data(self.aux_data.debug, self.aux_data.logger_active, self.aux_data.logger, "Ticket closed")

                        if team == "L1":
                            Utils.check_escalated_similar_tickets(curr_id, tickets_updated, tickets_inheritance, self.ticket_similarity_selector, self.subfamily_pool, True, self.aux_data)
                        
                        self.update_ticket_transfer_ticket(tickets_updated[curr_id], family_subtechniques)
                        Utils.update_analyst_data(tickets_updated[curr_id], curr_id, self.analysts_info)
                        Utils.remove_ticket_priority_queue(tickets_updated[curr_id], self.priority_queues)
                        self.update_steps_duration(tickets_updated[curr_id])
                        self.update_analysts_skill(tickets_updated[curr_id], self.analysts_info, self.subfamily_steps_speeds, self.aux_data.logger)

                        Utils.check_pending_tickets_priorities(self.analysts_info, analysts_in_shift, team, tickets_updated[curr_id]["allocated_tsp"], tickets_updated, self.priority_queues, self.aux_data)   
                        Utils.update_family_resolution(tickets_updated[curr_id], families_resolution)
                
                        if tickets_updated[curr_id]["replication_status"] != None:
                            #print(f'Ticket {curr_id} will be replicated due to {tickets_updated[curr_id]["replication_status"]}')
                            n_replicated = Utils.replicate_ticket(self.analysts_info.keys(), tickets_updated[curr_id], tickets, self.priority_queues, n_replicated, True, self.aux_data)
                    prev_shift = curr_shift
                    curr_id, original_dict_idx, curr_shift, analysts_in_shift = Utils.get_next_ticket(tickets_updated[curr_id], close_shift, curr_shift, analysts_in_shift, original_dict_idx, tickets_updated, original_keys, self.analysts_info, self.priority_queues, families_resolution[team], self.shifts, self.aux_data)  
                        
                wait_time, curr_time = Utils.get_function_time_spent(initial_time)
                #print(f'Time spent in treating the tickets: {wait_time} seconds')
                #Utils.debug_and_log_data(self.aux_data.debug, self.aux_data.logger_active, self.aux_data.logger, f'Number of Replicated Tickets: {n_replicated}')
                Utils.check_next_existing_teams(tickets, team)

        tickets_processed = Utils.process_tickets_solved(tickets, list(self.analysts_info.keys()), self.subfamily_pool, True, self.aux_data)
        return tickets_processed, family_subtechniques
   
    # Get the analysts available and returns
    def assign_analyst(self, ticket_id, curr_shift, analysts_in_shift, tickets_info, priority_queues, tickets_inheritance, locked, mode, generation, use_subfamily_action_choices, use_same_action_choices, family_subtechniques):

        ticket_tsp = tickets_info[ticket_id]["allocated_tsp"]        

        if analysts_in_shift:
            analysts_free = Utils.get_free_analysts_tsp(self.analysts_info[tickets_info[ticket_id]["team"]]["analysts"], analysts_in_shift, ticket_tsp, self.aux_data)
            if analysts_free:
                ticket_date = tickets_info[ticket_id]["allocated"]
                analysts_available = []
                close_shift = False
                
                for analyst in analysts_free:
                    Utils.debug_and_log_data(self.aux_data.debug, self.aux_data.logger_active, self.aux_data.logger, f'Current analyst: {analyst}')
                    analyst_sol, sol_status, new_action = self.check_next_analyst_action(tickets_info[ticket_id], analyst, self.subfamily_analysts_action, locked, use_subfamily_action_choices, use_same_action_choices)
                    act_dur, transitions = Utils.get_action_duration(tickets_info[ticket_id]["family"], analyst_sol, tickets_info[ticket_id]["team"], analyst, self.subfamily_steps_speeds[
                        tickets_info[ticket_id]["subfamily"]][tickets_info[ticket_id]["team"]][analyst], self.family_steps_pool, family_subtechniques, self.aux_data)
                    
                    valid_user = self.check_valid_analyst(tickets_info, ticket_date, tickets_info[ticket_id]["subfamily"], tickets_info[ticket_id]["team"], analyst, act_dur, tickets_info[ticket_id]["outlier"])
                    if valid_user:
                        self.update_subfamily_data(tickets_info[ticket_id]["subfamily"], tickets_info[ticket_id]["family"], tickets_info[ticket_id]["team"], analyst, analyst_sol, act_dur, transitions, None)
                        analysts_available.append(analyst)

                if analysts_available:
                    #tickets_info[ticket_id]["replication_status"] = None
                    Utils.debug_and_log_data(self.aux_data.debug, self.aux_data.logger_active, self.aux_data.logger, f'Analysts available: {analysts_available}')
                    
                    analyst, analyst_data = self.pick_analyst(tickets_info[ticket_id], analysts_available, mode)
                    self.check_similar_actions(tickets_info, tickets_info[ticket_id], family_subtechniques, analyst, analyst_data[analyst])
                    
                    if generation:
                        tickets_info[ticket_id]["analysts available"] = analysts_available
                
                    close_shift = Utils.check_close_sfift(self.priority_queues[tickets_info[ticket_id]["team"]], tickets_info, self.aux_data.logger)
                    return True, close_shift
                else:  
                    Utils.send_ticket_priority_queue(tickets_info[ticket_id], priority_queues, self.aux_data, 0)
                    close_shift = True
                    if "analysed_in_shift" not in tickets_info[ticket_id]:
                        tickets_info[ticket_id]["analysed_in_shift"] = curr_shift
                        Utils.log_data(self.aux_data.logger, f'id {tickets_info[ticket_id]["id"]} analysed in shift {curr_shift}')
            else:   
                Utils.send_ticket_priority_queue(tickets_info[ticket_id], self.priority_queues, self.aux_data, 1)
                close_shift = Utils.check_close_sfift(self.priority_queues[tickets_info[ticket_id]["team"]], tickets_info, self.aux_data.logger)
                return False, close_shift
        else:      
            Utils.send_ticket_priority_queue(tickets_info[ticket_id], priority_queues, self.aux_data, 2)
    
        return False, close_shift
        
    # Checks ticket status and updates transferred tickets
    def check_similar_actions(self, all_tickets, ticket, family_subtechniques, analyst, analyst_data):

        subfamily = ticket["subfamily"]
        team = ticket["team"]

        ticket['steps_transitions'] = self.subfamily_analysts_action[subfamily][team][analyst]['steps_dur']
        ticket["status"] = Utils.check_ticket_distance(ticket, analyst_data["action"], self.subfamily_pool[subfamily]["teams_actions"][team], self.actions_similarity, list(self.analysts_info.keys()), self.ticket_verification_selector)
        
        if ticket["status"] == "Transfer":
            ticket["replication_status"] = "Verification"
            
        #Utils.log_data(self.aux_data.logger, f'Ticket Status: {status}')
        Utils.update_data(ticket, allocated = ticket["allocated"], allocated_tsp = ticket["allocated_tsp"], analyst = analyst, action = analyst_data["action"], duration = analyst_data["duration"])

    def update_ticket_transfer_ticket(self, ticket, family_subtechniques):
        
        ticket_date = ticket["allocated"]
        
        if ticket["replication_status"] != None:
            subfamily = ticket["subfamily"]
            team = ticket["team"]
            analyst = ticket["analyst"]
            
            Utils.log_data(self.aux_data.logger, f'Prev escalated: {ticket["action"]}')
            opt_transfer_picked = random.choice(list(self.special_steps["transfer_opt"].keys()))
            action = Utils.convert_to_escaleted_action(ticket, ticket["action"], (opt_transfer_picked, self.special_steps["transfer_opt"][opt_transfer_picked]))

            if opt_transfer_picked not in self.family_steps_pool[ticket["team"]][ticket["family"]]["transfer_opt"]:
                self.family_steps_pool[ticket["team"]][ticket["family"]]["transfer_opt"][opt_transfer_picked] = self.special_steps["transfer_opt"][opt_transfer_picked]
                
            action = self.initiate_steps_speeds(subfamily, team, analyst, action)
            action_dur, action_transitions = Utils.get_action_duration(ticket["family"], action, team, analyst, self.subfamily_steps_speeds[subfamily][team][analyst], self.family_steps_pool, family_subtechniques, self.aux_data)
            Utils.log_data(self.aux_data.logger, f'Action escalated: {action}')

            if Utils.check_shift_ending(ticket_date, action_dur, self.aux_data.debug):
                Utils.debug_and_log_data(self.aux_data.debug, self.aux_data.logger_active, self.aux_data.logger, "Analyst working after his shift ends!")
                
            Utils.update_data(ticket, action = action, duration = action_dur, steps_transitions = action_transitions)
        
        self.update_ticket_duration(ticket)
        ticket['fixed'] = ticket_date + timedelta(0, 0, 0, 0, ticket["duration_outlier"])
        ticket['fixed_tsp'] = ticket['allocated_tsp'] + (60 * ticket["duration_outlier"]) 
        #Utils.log_data(self.aux_data.logger, f'Allocated: {ticket_date}')
        Utils.log_data(self.aux_data.logger, f'Fixed: {ticket["fixed"]}')

    # Verifies if a subfamily already has a member allocated to a ticket with a specific action
    def check_next_analyst_action(self, ticket, analyst, subfamily_actions, special_tech, use_subfamily_action_choices, use_same_action_choices):

        family = ticket["family"]
        subfamily = ticket["subfamily"]
        team = ticket["team"]
        Utils.debug_code(self.aux_data.debug, f'Family: {family}, Subfamily: {subfamily}, Team: {team}, Analyst: {analyst}')

        analyst_sol, actions_status = "", ""
        new_action = True
        # Team Analyst already solved the family
        if subfamily in subfamily_actions.keys() and team in subfamily_actions[subfamily].keys() and analyst in subfamily_actions[subfamily][team].keys():
            Utils.debug_and_log_data(self.aux_data.debug, self.aux_data.logger_active, self.aux_data.logger,  "Gen: Subfamily and team member already exists!")
            same_action = next(use_same_action_choices.generate())
            if same_action:
                new_action = False
                analyst_sol = subfamily_actions[subfamily][team][analyst]['action']
                Utils.debug_and_log_data(self.aux_data.debug, self.aux_data.logger_active, self.aux_data.logger, f'Gen: {analyst} is going to use the prev action {analyst_sol}')
                actions_status = f'{analyst} is using the same action'
            else:
                analyst_sol = Utils.build_analyst_action(family, subfamily, team, analyst, self.subfamily_pool[subfamily]["teams_actions"][team], self.family_steps_pool[team], special_tech, self.aux_data)
                Utils.debug_and_log_data(self.aux_data.debug, self.aux_data.logger_active, self.aux_data.logger, f'Gen: {analyst} is performing a new action: {analyst_sol}')
                actions_status = f'{analyst} is using a new action'
        else:
            Utils.debug_and_log_data(self.aux_data.debug, self.aux_data.logger_active, self.aux_data.logger, "Gen: Subfamily and team member don't exists!")
            use_subfamily_action = next(use_subfamily_action_choices.generate())
            # Uses the subfamily action
            if use_subfamily_action:
                analyst_sol = self.subfamily_pool[subfamily]["teams_actions"][team]
                Utils.debug_and_log_data(self.aux_data.debug, self.aux_data.logger_active, self.aux_data.logger, f'Gen: {analyst} is going to use the subfamily action: {analyst_sol}')
                actions_status = f'{analyst} is using the subfamily action'
            # Creates a new action based on the family
            else:
                analyst_sol = Utils.build_analyst_action(family, subfamily, team, analyst, self.subfamily_pool[subfamily]["teams_actions"][team], self.family_steps_pool[team], special_tech, self.aux_data)
                Utils.debug_and_log_data(self.aux_data.debug, self.aux_data.logger_active, self.aux_data.logger, f'Gen: {analyst} is going to use a new action: {analyst_sol}')
                actions_status = f'{analyst} is going to use new action'

        analyst_sol = self.initiate_steps_speeds(subfamily, team, analyst, analyst_sol)
        return analyst_sol, actions_status, new_action

    # Instantiates the dictionary with the information about the analyst-steps used in each subfamily
    def initiate_steps_speeds(self, subfamily, team, member, action):

        action = Utils.change_action_format(action)
        # print(action)
        for step in action:
            # print(step)
            if subfamily not in self.subfamily_steps_speeds.keys():
                self.subfamily_steps_speeds[subfamily] = {}

            if team not in self.subfamily_steps_speeds[subfamily].keys():
                self.subfamily_steps_speeds[subfamily][team] = {}

            if member not in self.subfamily_steps_speeds[subfamily][team].keys():
                self.subfamily_steps_speeds[subfamily][team][member] = {}

            if step not in self.subfamily_steps_speeds[subfamily][team][member].keys():
                self.subfamily_steps_speeds[subfamily][team][member][step] = {}
                curr_learning = random.uniform(0.01, 0.1)
                speed = Utils.get_speed(self.analysts_info[team]["analysts"][member]["growth"], curr_learning)
                target_speed = round(random.uniform(0.2, speed), 2)
                max_counter = random.randint(self.min_learning_counter, self.max_learning_counter)
                Utils.update_data(self.subfamily_steps_speeds[subfamily][team][member][step], speed = speed, target_speed = target_speed, learning_rate = curr_learning, max_counter = max_counter, curr_counter = 0, last_incident = -1)
                
        return action

    # Checks if analyst action surpasses their shift
    def check_valid_analyst(self, all_tickets, ticket_date, subfamily, team, member, action_duration, outlier):
        
        action_duration = Utils.get_action_duration_outlier(action_duration, outlier, self.aux_data.outlier_cost)
        if not Utils.check_shift_ending(ticket_date, action_duration, self.aux_data.debug):
            user_status= True
            Utils.debug_and_log_data(self.aux_data.debug, self.aux_data.logger_active, self.aux_data.logger, f'Curr Date: {ticket_date} {member} - action dur - {action_duration}')
        else:
            user_status= False
            Utils.debug_and_log_data(self.aux_data.debug, self.aux_data.logger_active, self.aux_data.logger, f'Curr Date: {ticket_date} {member} - surpassing his shift - {action_duration}')

        return user_status

    # Updates the data of the ticket subfamily
    def update_subfamily_data(self, subfamily, family, team, member, analyst_sol, action_dur, steps_dur, special):

        #print(f'Data updated on {member} and {subfamily}')
        if subfamily not in self.subfamily_analysts_action.keys():
            self.subfamily_analysts_action[subfamily] = {}

        if team not in self.subfamily_analysts_action[subfamily].keys():
            self.subfamily_analysts_action[subfamily][team] = {}

        if member not in self.subfamily_analysts_action[subfamily][team].keys():
            self.subfamily_analysts_action[subfamily][team][member] = {}
    
        Utils.update_data(self.subfamily_analysts_action[subfamily][team][member], action = analyst_sol, duration = action_dur, steps_dur = steps_dur)

    # Finds the user according to the mode chosen (default is 0) and scheduling status
    def pick_analyst(self, ticket, analysts_available, mode):

        team = ticket["team"]
        subfamily = ticket["subfamily"]
    
        if mode == 0:
            analyst = self.find_free_analyst(ticket, analysts_available)
        else:
            analyst = self.find_next_fastest_analyst(ticket, analysts_available)

        #print("Analyst:", analyst)
        analyst_data = {}
        analyst_data[analyst] = {}
        
        analyst_data[analyst]["action"] = list(self.subfamily_analysts_action[subfamily][team][analyst]["action"])
        analyst_data[analyst]["duration"] = float(self.subfamily_analysts_action[subfamily][team][analyst]["duration"])
        #analyst_data[analyst]["duration_outlier"] = Utils.get_action_duration_outlier(self.subfamily_analysts_action[subfamily][team][analyst]['duration'], outlier, self.aux_data.outlier_cost)
        
        Utils.debug_and_log_data(self.aux_data.debug, self.aux_data.logger_active, self.aux_data.logger, f'Analyst: {analyst}, data: {analyst_data[analyst]}')
        return analyst, analyst_data

    # Gets a free analyst
    def find_free_analyst(self, ticket, team_analysts):

        analyst = None
        # This prevents from assigning always the same user
        temp = random.sample(team_analysts, len(team_analysts))
        analyst = random.choice(temp)
        return analyst

    # Finds the next fastest analyst
    def find_next_fastest_analyst(self, ticket, analysts_available):

        free_users = []
        team = ticket["team"]
        subfamily = ticket["subfamily"]

        for x in analysts_available:
            if not self.analysts_info[team]["analysts"][x]["queue"]:
                free_users.append(x)

        #print("Free Users", free_users)
        if len(free_users) == 1:
            return free_users[0]
        else:
            user = None
            time = 0
            for i in self.analysts_info[team]["analysts"]:
                if i in free_users:
                    # print("User:", i)
                    if subfamily not in self.analysts_info[team]["analysts"][i]["summary"].keys():
                        #print(f'{i} did not handle this subfamily!')
                        time_spent = 0
                    else:
                        time_spent = self.analysts_info[team]["analysts"][i]["summary"][subfamily]["Time spent"]
                        #print(f'{i} spent {time_spent} in the subfamily')
                        # print("Number of occurences", self.analysts_info[team][i]["summary"][subfamily]["occurences"])

                    if ticket['outlier']:
                        action_dur = self.subfamily_analysts_action[subfamily][team][i]['duration'] + \
                            self.aux_data.outlier_cost * self.subfamily_analysts_action[subfamily][team][i]['duration']
                    else:
                        action_dur = self.subfamily_analysts_action[subfamily][team][i]['duration']

                    time_temp = time_spent + action_dur
                    # print("Action Duration:", action_dur)
                    # print("Total Time:", time_temp)

                    if time == 0:
                        time = time_temp
                        user = i
                    elif time_temp < time:
                        time = time_temp
                        user = i
            # print("User", user)
            if self.analysts_info[team]["analysts"][user]["queue"]:
                Utils.debug_and_log_data(self.aux_data.debug, self.aux_data.logger_active, self.aux_data.logger, f'{user} is occupied until {self.analysts_info[team]["analysts"][user]["queue"][-1]}')
                user = None

            return user

    # Updates the ticket duration with/without outliers
    def update_ticket_duration(self, ticket):

        if ticket['outlier']:
            ticket['duration_outlier'] = ticket["duration"] + self.aux_data.outlier_cost * ticket["duration"]
        else:
            ticket['duration_outlier'] = ticket["duration"]
        # ticket['duration no speed'] = action_dur * self.subfamily_steps_speeds[subfamily][team][member][step]

    ######################## Analyst Operations ########################

    # Improves analyst's speed
    def improve_skill(self, ticket, analysts_info, subfamily_steps_speeds, logger):

        action = ticket["action"]
        subfamily = ticket["subfamily"]
        curr_date = ticket["allocated_tsp"]
        team = ticket["team"]
        analyst = ticket["analyst"]

        for step in action:
            if subfamily_steps_speeds[subfamily][team][analyst][step]["curr_counter"] == subfamily_steps_speeds[subfamily][team][analyst][step]["max_counter"]:
                #Utils.log_data(self.logger, f'Improve skill of {analyst} on step {step}')
                subfamily_steps_speeds[subfamily][team][analyst][step]["last_incident"] = curr_date
                #print("Last incident updated:", curr_date)
                learning_rate, speed_updated = Utils.update_step_speed(subfamily_steps_speeds[subfamily][team][analyst], step, analysts_info[team]["analysts"][analyst]["growth"], "improve")
                if speed_updated > 0.2:
                    target_speed = subfamily_steps_speeds[subfamily][team][analyst][step]["target_speed"]
                    if speed_updated > target_speed:
                        #Utils.log_data(self.logger, f'Updated speed: {speed_updated}, learning rate updated: {learning_rate}')
                        subfamily_steps_speeds[subfamily][team][analyst][step]["learning_rate"] = learning_rate
                        subfamily_steps_speeds[subfamily][team][analyst][step]["speed"] = speed_updated
                        subfamily_steps_speeds[subfamily][team][analyst][step]["curr_counter"] = 0
                    #print("Analyst updated info:", other_params["analysts_skills"][team][analyst])
                    # else:
                    #    print(f'{analyst} already reached speed intended!')
                # else:
                #    print(f'{step} cannot be improved anymore!')

    # Deteriorates analyst's speed
    def lose_skill(self, ticket, analysts_info, subfamily_steps_speeds, logger):

        subfamily = ticket["subfamily"]
        curr_date = ticket["allocated_tsp"]
        team = ticket["team"]
        analyst = ticket["analyst"]
        action = ticket["action"]

        # 1440 min -> 1 day
        for step in subfamily_steps_speeds[subfamily][team][analyst]:
            if subfamily_steps_speeds[subfamily][team][analyst][step]["last_incident"] != -1 and step not in action:
                #print("Last incident:", subfamily_steps_speeds[subfamily][team][analyst][step]["last incident"])
                time_diff = Utils.calculate_timestamp_diff(subfamily_steps_speeds[subfamily][team][analyst][step]["last_incident"], curr_date, "minutes")
                if time_diff > 10080:  # 1 week
                    #Utils.log_data(self.logger, "More than 1 week has passed")
                    subfamily_steps_speeds[subfamily][team][analyst][step]["last_incident"] = curr_date
                    if subfamily_steps_speeds[subfamily][team][analyst][step]["speed"] < 1.98:
                        #Utils.log_data(self.logger, f'Lose skill of {analyst} on step {step}')

                        learning_rate, speed_updated = Utils.update_step_speed(subfamily_steps_speeds[subfamily][team][analyst], step, analysts_info[team]["analysts"][analyst]["growth"], "worsen")
                        if speed_updated < 2:
                            #Utils.log_data(self.logger, f'Updated speed: {speed_updated}, learning rate updated: {learning_rate}')
                            subfamily_steps_speeds[subfamily][team][analyst][step]["learning_rate"] = learning_rate
                            subfamily_steps_speeds[subfamily][team][analyst][step]["speed"] = speed_updated
                            subfamily_steps_speeds[subfamily][team][analyst][step]["curr_counter"] = 0
                        # else:
                        #    print(f'{analyst} step cannot be slower')

    # Updates analyst's skill
    def update_analysts_skill(self, ticket, analysts_info, subfamily_steps_speeds, logger):

        self.improve_skill(ticket, analysts_info, subfamily_steps_speeds, logger)
        self.lose_skill(ticket, analysts_info, subfamily_steps_speeds, logger)