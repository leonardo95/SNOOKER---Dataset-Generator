"""
Created on Mon Feb  6 11:05:57 2023

@author: Leonardo Ferreira
"""

from Code.Utils import Utils, BufferedRandomChoiceGenerator

import random
from datetime import datetime, timedelta

class AnalystEmulation:

    def __init__(self, gen_id, treatment_params, analysts_info, family_pool, subfamily_pool, family_steps_pool, special_steps, shifts, aux_data, seed):
        """
        Initiates data relevant to ticket treatment

        Parameters
        ----------
        gen_id : str
            Unique generation identifier.
        treatment_params : dict
            Comprises all data about parameters related to ticket treatment.
        analysts_info : dict
            Comprises all data about teams and their operators.
        family_pool : dict
            Comprises data about the families.
        subfamily_pool : dict
            Comprises data about the subfamilies.
        family_steps_pool : dict
            Comprises data about the techniques and subfamilies for each family treatment.
        special_steps : dict
            Comprises information about special steps.
        shifts : dict
            Comprises information about the work shifts.
        aux_data : UtilsParams
            Comprises auxiliar data, including outlier, priority levels, and other features.
        seed : int
            Seed value for random processes.

        Returns
        -------
        None.

        """
        self._id = gen_id
        self.subfamily_analysts_action, self.subfamily_steps_speeds = {}, {}
        self.analyst_subfamily_action_probability = treatment_params["analyst_subfamily_action_probability"]
        self.analyst_same_action_probability = treatment_params["analyst_same_action_probability"]
        self.min_learning_counter = treatment_params["min_learning_counter"]
        self.max_learning_counter = treatment_params["max_learning_counter"]
        self.actions_similarity = treatment_params["actions_similarity"]
        self.shifts = shifts
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

    def update_steps_duration(self, ticket):
        """
        Updates the speed of each analyst-step.

        Parameters
        ----------
        ticket : dict
            Ticket being analyzed.

        Returns
        -------
        None.

        """
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
            step_date += step_dur

    #@profile
    def process_tickets(self, thread_canceled, weight, tickets):
        """
        Main Ticket Handler - Allocates an analyst and action to each ticket

        Parameters
        ----------
        thread_canceled : bool
            Thread status (cancels generation if TRUE).
        weight : int
            Used for the interface progress bar (deprecated).
        tickets : dict
            Comprises the tickets requesting treatment.

        Returns
        -------
        tickets_processed : dict
            Comprises the tickets treated.
        family_subtechniques : dict
            Comprises all techniques and subtechniques employed in the ticket families analyzed
            
        """
        
        Utils.debug_and_log_data(self.aux_data.debug, self.aux_data.logger, "\nProcess tickets")
        initial_time = datetime.now()
        mode = 0
        tickets_inheritance, families_resolution = {}, {}
        
        locked_techniques = Utils.get_locked_techniques(self.special_steps)
        family_subtechniques = Utils.get_family_middle_subtechniques(self.family_steps_pool)
        Utils.set_seed(self.seed)
        first_team = list(self.analysts_info.keys())[0]
        last_team = list(self.analysts_info.keys())[-1]

        for team in self.priority_queues:
            print("team:", team)
            if team in tickets:
                Utils.debug_and_log_data(self.aux_data.debug, self.aux_data.logger, f'Analyse tickets in {team}')
                curr_id, original_dict_idx, n_replicated = 0, 0, 0
    
                tickets_updated = tickets[team]
                if team != first_team:
                    tickets_inheritance = {}

                use_subfamily_action_choices = BufferedRandomChoiceGenerator([True, False], [self.analyst_subfamily_action_probability, 1 - self.analyst_subfamily_action_probability], 5000)
                use_same_action_choices = BufferedRandomChoiceGenerator([True, False], [self.analyst_same_action_probability, 1 - self.analyst_same_action_probability], 5000)
                original_keys = list(tickets_updated.keys())

                curr_shift = Utils.get_ticket_shift(tickets_updated[curr_id]["allocated"].time(), self.shifts)
                prev_shift = curr_shift
                analysts_in_shift = Utils.get_operators_in_shift(self.analysts_info[team], curr_shift)
        
                while curr_id != None:   
                    print("Ticket id:", curr_id)
                    Utils.update_analysts_in_next_shift(self.analysts_info[team]["analysts"], team, tickets_updated[curr_id]["allocated"], prev_shift, curr_shift, self.analysts_info, None, self.shifts, self.aux_data)
                    Utils.debug_and_log_data(self.aux_data.debug, self.aux_data.logger, f'Ticket id: {curr_id}, Allocated: {tickets_updated[curr_id]["allocated"]}, Priority: {tickets_updated[curr_id]["priority"]}')

                    if team == first_team:
                        Utils.check_escalated_similar_tickets(curr_id, tickets_updated, tickets_inheritance, self.ticket_similarity_selector, self.subfamily_pool, last_team, self.aux_data)
                    
                    ticket_closed, close_shift = self.assign_analyst(curr_id, curr_shift, analysts_in_shift, tickets_updated, self.priority_queues, tickets_inheritance, locked_techniques, mode, use_subfamily_action_choices, use_same_action_choices, family_subtechniques)

                    if ticket_closed:    
                        Utils.debug_and_log_data(self.aux_data.debug, self.aux_data.logger, "Ticket closed")
                        self.update_ticket_transfer_ticket(tickets_updated[curr_id], family_subtechniques)
                        Utils.update_analyst_data(tickets_updated[curr_id], curr_id, self.analysts_info)
                        Utils.remove_ticket_priority_queue(tickets_updated[curr_id], self.priority_queues)
                        self.update_steps_duration(tickets_updated[curr_id])
                        self.update_analysts_skill(tickets_updated[curr_id], self.analysts_info, self.subfamily_steps_speeds)

                        Utils.check_pending_tickets_priorities(self.analysts_info, analysts_in_shift, team, tickets_updated[curr_id]["allocated_tsp"], tickets_updated, self.priority_queues, self.aux_data)   
                        Utils.update_family_resolution(tickets_updated[curr_id], families_resolution)
                
                        if tickets_updated[curr_id]["replication_status"] != None:
                            Utils.debug_and_log_data(True, self.aux_data.logger, f'Ticket {curr_id} will be replicated due to {tickets_updated[curr_id]["replication_status"]}')
                            n_replicated = Utils.replicate_ticket(self.analysts_info.keys(), tickets_updated[curr_id], tickets, self.priority_queues, n_replicated, self.aux_data)
                            
                    prev_shift = curr_shift
                    curr_id, original_dict_idx, curr_shift, analysts_in_shift = Utils.get_next_ticket(tickets_updated[curr_id], close_shift, curr_shift, analysts_in_shift, original_dict_idx, tickets_updated, original_keys, self.analysts_info, self.priority_queues, families_resolution[team], self.shifts, self.aux_data)

                wait_time, curr_time = Utils.get_function_time_spent(initial_time)
                Utils.debug_and_log_data(self.aux_data.debug, self.aux_data.logger, f'Number of Replicated Tickets: {n_replicated}. \nTime spent in treating the tickets: {wait_time} seconds')
                Utils.check_next_existing_teams(tickets, team)

        tickets_processed = Utils.process_tickets_solved(tickets, list(self.analysts_info.keys()), self.subfamily_pool, self.aux_data.logger)
        #print("Aqui:", tickets_processed)
        return tickets_processed, family_subtechniques
   
    def assign_analyst(self, ticket_id, curr_shift, analysts_in_shift, tickets_info, priority_queues, tickets_inheritance, locked, mode, use_subfamily_action_choices, use_same_action_choices, family_subtechniques):
        """
        Assigns an analyst and action after assessing the operators and actions available for ticket treatment

        Parameters
        ----------
        ticket_id : int
            Ticket identifier.
        curr_shift : int
            Work shift being analyzed.
        analysts_in_shift : list
            Operators working in the work shift analyzed.
        tickets_info : dict
            Comprises information about all tickets.
        priority_queues : dict
            Comprises information about the priority queues in the team being analyzed (has different priority levels).
        tickets_inheritance : dict
            Comprises information about ticket similarity (in terms of client and subfamily).
        locked : dict
            List of techniques that can not be used for operator-action generation, like initiate, end, and transfer steps.
        mode : int
            0 - Find first free operator; else - find next fastest operator.
        use_subfamily_action_choices : BufferedRandomChoiceGenerator            
            Generator that tells whether an operator should use the subfamily action or not.
        use_same_action_choices : BufferedRandomChoiceGenerator
            Generator that tells whether an operator should use a similar action to another employed in previous treatments.
        family_subtechniques : dict
            Comprises all techniques and subtechniques employed in the ticket families analyzed.
        
        Returns
        -------
        bool
            Ticket closed or not.
        close_shift : bool
            True to jump to the next priority level to review the remaining pending tickets.
            
        """
        ticket_tsp = tickets_info[ticket_id]["allocated_tsp"]   
        if analysts_in_shift:
            analysts_free = Utils.get_free_analysts_tsp(self.analysts_info[tickets_info[ticket_id]["team"]]["analysts"], analysts_in_shift, ticket_tsp, self.aux_data, False)
            if analysts_free:
                Utils.debug_and_log_data(self.aux_data.debug, self.aux_data.logger, f'Operators available in shift: {analysts_free}')
                ticket_date = tickets_info[ticket_id]["allocated"]
                analysts_available = []
                close_shift = False
                
                for analyst in analysts_free:
                    Utils.debug_and_log_data(self.aux_data.debug, self.aux_data.logger, f'Current analyst: {analyst}')
                    analyst_sol, sol_status, new_action = self.check_next_analyst_action(tickets_info[ticket_id], analyst, self.subfamily_analysts_action, locked, use_subfamily_action_choices, use_same_action_choices)
                    act_dur, transitions = Utils.get_action_duration(tickets_info[ticket_id]["family"], analyst_sol, tickets_info[ticket_id]["team"], analyst, self.subfamily_steps_speeds[tickets_info[ticket_id]["subfamily"]][tickets_info[ticket_id]["team"]][analyst], self.family_steps_pool, family_subtechniques, self.aux_data)
                    
                    valid_operator = self.check_valid_analyst(tickets_info, ticket_date, tickets_info[ticket_id]["subfamily"], tickets_info[ticket_id]["team"], analyst, act_dur, tickets_info[ticket_id]["outlier"])
                    if valid_operator:
                        self.update_subfamily_data(tickets_info[ticket_id]["subfamily"], tickets_info[ticket_id]["family"], tickets_info[ticket_id]["team"], analyst, analyst_sol, act_dur, transitions)
                        analysts_available.append(analyst)

                if analysts_available:
                    Utils.debug_and_log_data(self.aux_data.debug, self.aux_data.logger, f'Analysts available: {analysts_available}')
                    analyst, analyst_data = self.pick_analyst(tickets_info[ticket_id], analysts_available, mode)
                    self.check_similar_actions(tickets_info, tickets_info[ticket_id], family_subtechniques, analyst, analyst_data[analyst])
                    tickets_info[ticket_id]["analysts available"] = analysts_available
        
                    close_shift = Utils.check_close_shift(self.priority_queues[tickets_info[ticket_id]["team"]], tickets_info, self.aux_data)
                    return True, close_shift
                else:  
                    Utils.send_ticket_priority_queue(tickets_info[ticket_id], priority_queues, self.aux_data, 0)
                    close_shift = True
                    if "analyzed_in_shift" not in tickets_info[ticket_id]:
                        tickets_info[ticket_id]["analyzed_in_shift"] = curr_shift
                        Utils.debug_and_log_data(self.aux_data.debug, self.aux_data.logger, f'Ticket {tickets_info[ticket_id]["id"]} analyzed in shift {curr_shift}')
            else:   
                Utils.send_ticket_priority_queue(tickets_info[ticket_id], self.priority_queues, self.aux_data, 1)
                close_shift = Utils.check_close_shift(self.priority_queues[tickets_info[ticket_id]["team"]], tickets_info, self.aux_data)

                return False, close_shift
        else:      
            Utils.send_ticket_priority_queue(tickets_info[ticket_id], priority_queues, self.aux_data.logger, 2)
    
        return False, close_shift
        
    def check_similar_actions(self, all_tickets, ticket, family_subtechniques, analyst, analyst_data):
        """
        Checks ticket status and updates transferred tickets.

        Parameters
        ----------
        all_tickets : dict
            Comprises information about all tickets within the team being analyzed.
        ticket : dict
            Current ticket being analyzed.
        family_subtechniques : dict
            Comprises all techniques and subtechniques employed in the families analyzed.
        analyst : str
            Operator picked for ticket treatment.
        analyst_data : dict
            Comprises information about the operator in terms of treatment.

        Returns
        -------
        None.

        """
        subfamily = ticket["subfamily"]
        team = ticket["team"]

        ticket['steps_transitions'] = self.subfamily_analysts_action[subfamily][team][analyst]['steps_dur']
        if ticket["replication_status"] == None:
            ticket["status"] = Utils.check_ticket_distance(ticket, analyst_data["action"], self.subfamily_pool[subfamily]["teams_actions"][team], self.actions_similarity, list(self.analysts_info.keys()), self.ticket_verification_selector)

            if ticket["status"] == "Transfer":
                ticket["replication_status"] = "Verification"
                Utils.debug_and_log_data(self.aux_data.debug, self.aux_data.logger, "To replicate due to distant actions")
            
        Utils.update_data(ticket, allocated = ticket["allocated"], allocated_tsp = ticket["allocated_tsp"], analyst = analyst, action = analyst_data["action"], duration = analyst_data["duration"])

    def update_ticket_transfer_ticket(self, ticket, family_subtechniques):
        """
        Updates a ticket that requires replication (action and its duration is updated).

        Parameters
        ----------
        ticket : dict
            Current ticket being analyzed.
        family_subtechniques : dict
            Comprises all techniques and subtechniques employed in the ticket family.
        is_generator : bool
            Whether this process is used exclusively in SNOOKER evaluation or not (could be evaluate other systems).

        Returns
        -------
        None.

        """
        ticket_date = ticket["allocated"]
        
        if ticket["replication_status"] != None:
            subfamily = ticket["subfamily"]
            team = ticket["team"]
            analyst = ticket["analyst"]
            
            Utils.debug_and_log_data(self.aux_data.debug, self.aux_data.logger, f'Action before escalation: {ticket["action"]}')
            opt_transfer_picked = random.choice(list(self.special_steps["transfer_opt"].keys()))
            action = Utils.convert_to_escaleted_action(ticket, list(ticket["action"]), (opt_transfer_picked, self.special_steps["transfer_opt"][opt_transfer_picked]))
            Utils.debug_and_log_data(self.aux_data.debug, self.aux_data.logger, f'Action after escalation: {ticket["action"]}')

            if opt_transfer_picked not in self.family_steps_pool[ticket["team"]][ticket["family"]]["transfer_opt"]:
                self.family_steps_pool[ticket["team"]][ticket["family"]]["transfer_opt"][opt_transfer_picked] = self.special_steps["transfer_opt"][opt_transfer_picked]
                
            action = self.initiate_steps_speeds(subfamily, team, analyst, action, self.aux_data.debug)
            action_dur, action_transitions = Utils.get_action_duration(ticket["family"], action, team, analyst, self.subfamily_steps_speeds[subfamily][team][analyst], self.family_steps_pool, family_subtechniques, self.aux_data)

            if Utils.check_shift_ending(ticket_date, action_dur, self.shifts, self.aux_data):
                Utils.debug_and_log_data(self.aux_data.debug, self.aux_data.logger, "Analyst working after his shift ends!")
                
            Utils.update_data(ticket, action = action, duration = action_dur, steps_transitions = action_transitions)
        
        self.update_ticket_duration(ticket)
            
        ticket['fixed'] = ticket_date + timedelta(0, 0, 0, 0, ticket["duration_outlier"])
        ticket['fixed_tsp'] = ticket['allocated_tsp'] + (60 * ticket["duration_outlier"]) 
        Utils.debug_and_log_data(self.aux_data.debug, self.aux_data.logger, f'Allocation date: {ticket_date} - Fixed: {ticket["fixed"]}')

    def check_next_analyst_action(self, ticket, analyst, subfamily_actions, special_tech, use_subfamily_action_choices, use_same_action_choices):
        """
        Action handler for operator-action assessment. New actions can be built or reused.

        Parameters
        ----------
        ticket : dict
            Current ticket being analyzed.
        analyst : str
            Operator picked for ticket treatment.
        subfamily_actions : dict
            Comprises information about the actions used in the subfamily treatment.
        special_tech : dict
            List of techniques that can not be used for operator-action generation, like initiate, end, and transfer steps.
        use_subfamily_action_choices : BufferedRandomChoiceGenerator            
            Generator that tells whether an operator should use the subfamily action or not.
        use_same_action_choices : BufferedRandomChoiceGenerator
            Generator that tells whether an operator should use a similar action to another employed in previous treatments.

        Returns
        -------
        analyst_sol : str
            Action chosen by the operator for ticket treatment.
        actions_status : str
            An operator may used the same action, use a new action, or use the subfamily action.
        new_action : bool
            Whether it corresponds to a new or known action.

        """
        family = ticket["family"]
        subfamily = ticket["subfamily"]
        team = ticket["team"]
        Utils.debug_and_log_data(self.aux_data.debug, self.aux_data.logger, f'Family: {family}, Subfamily: {subfamily}, Team: {team}, Analyst: {analyst}')

        analyst_sol, actions_status = "", ""
        new_action = True
        # Team and analyst already solved the family
        if subfamily in subfamily_actions.keys() and team in subfamily_actions[subfamily].keys() and analyst in subfamily_actions[subfamily][team].keys():
            Utils.debug_and_log_data(self.aux_data.debug, self.aux_data.logger, "Gen: Subfamily and team member already exists!")
            same_action = next(use_same_action_choices.generate())
            
            if same_action:
                new_action = False
                analyst_sol = subfamily_actions[subfamily][team][analyst]['action']
                Utils.debug_and_log_data(self.aux_data.debug, self.aux_data.logger, f'{analyst} is going to use the previous action: {analyst_sol}')
                actions_status = f'{analyst} is using the same action'
            else:
                analyst_sol = Utils.build_analyst_action(family, subfamily, team, analyst, self.subfamily_pool[subfamily]["teams_actions"][team], self.family_steps_pool[team], special_tech, self.aux_data)
                Utils.debug_and_log_data(self.aux_data.debug, self.aux_data.logger, f'{analyst} is performing a new action: {analyst_sol}')
                actions_status = f'{analyst} is using a new action'
        else:
            Utils.debug_and_log_data(self.aux_data.debug, self.aux_data.logger, "Gen: Subfamily and team member don't exist!")
            use_subfamily_action = next(use_subfamily_action_choices.generate())

            if use_subfamily_action:
                analyst_sol = self.subfamily_pool[subfamily]["teams_actions"][team]
                Utils.debug_and_log_data(self.aux_data.debug, self.aux_data.logger, f'{analyst} is going to use the subfamily action: {analyst_sol}')
                actions_status = f'{analyst} is using the subfamily action'
            else:
                analyst_sol = Utils.build_analyst_action(family, subfamily, team, analyst, self.subfamily_pool[subfamily]["teams_actions"][team], self.family_steps_pool[team], special_tech, self.aux_data)
                Utils.debug_and_log_data(self.aux_data.debug, self.aux_data.logger, f'{analyst} is going to use a new action: {analyst_sol}')
                actions_status = f'{analyst} is going to use new action'

        analyst_sol = self.initiate_steps_speeds(subfamily, team, analyst, analyst_sol, self.aux_data.debug)
        return analyst_sol, actions_status, new_action

    def initiate_steps_speeds(self, subfamily, team, operator, action, debug):
        """
        Instantiates the subfamily_steps_speeds dictionary with the information about the analyst-steps used in each subfamily.

        Parameters
        ----------
        subfamily : str
            Current subfamily being analyzed.
        team : str
            Current team being analyzed.
        operator : str
            Current operator being analyzed.
        action : str
            Action chosen by the operator for ticket treatment.

        Returns
        -------
        action : str
            Same action but with different format (as a list)

        """
        action = Utils.change_action_format(action)

        for step in action:
            if subfamily not in self.subfamily_steps_speeds.keys():
                self.subfamily_steps_speeds[subfamily] = {}

            if team not in self.subfamily_steps_speeds[subfamily].keys():
                self.subfamily_steps_speeds[subfamily][team] = {}

            if operator not in self.subfamily_steps_speeds[subfamily][team].keys():
                self.subfamily_steps_speeds[subfamily][team][operator] = {}

            if step not in self.subfamily_steps_speeds[subfamily][team][operator].keys():
                self.subfamily_steps_speeds[subfamily][team][operator][step] = {}
                curr_learning = random.uniform(0.01, 0.1)
                speed = Utils.get_speed(self.analysts_info[team]["analysts"][operator]["growth"], curr_learning)
                target_speed = round(random.uniform(0.2, speed), 2)
                max_counter = random.randint(self.min_learning_counter, self.max_learning_counter)
                Utils.update_data(self.subfamily_steps_speeds[subfamily][team][operator][step], speed = speed, target_speed = target_speed, learning_rate = curr_learning, max_counter = max_counter, curr_counter = 0, last_incident = -1)
                
        return action

    def check_valid_analyst(self, all_tickets, ticket_date, subfamily, team, operator, action_duration, outlier):
        """
        Checks if operator-action surpasses their shift.

        Parameters
        ----------
        all_tickets : dict
            Comprises information about all tickets within the team being analyzed.
        ticket_date : datetime
            Allocated datetime of the ticket.
        subfamily : str
            Current subfamily being analyzed.
        team : str
            Current team being analyzed.
        operator : str
            Current operator being analyzed.
        action_duration : float
            Action duration required for ticket treatment.

        Returns
        -------
        operator_status : bool
            Wether the action causes the operator to surpass its work shift.

        """
        action_duration = Utils.get_action_duration_outlier(action_duration, outlier, self.aux_data.outlier_cost)
        if not Utils.check_shift_ending(ticket_date, action_duration, self.shifts, self.aux_data):
            operator_status = True
            Utils.debug_and_log_data(self.aux_data.debug, self.aux_data.logger, f'Current Date: {ticket_date}, {operator} takes {action_duration} min')
        else:
            operator_status = False
            Utils.debug_and_log_data(self.aux_data.debug, self.aux_data.logger, f'Curr Date: {ticket_date}, {operator} surpasses shift with action taking {action_duration}')

        return operator_status

    def update_subfamily_data(self, subfamily, family, team, operator, analyst_sol, action_dur, steps_dur):
        """
        Updates the data of the ticket subfamily.

        Parameters
        ----------
        subfamily : str
            Current subfamily being analyzed.
        family : str
            Current family being analyzed.
        team : str
            Current team being analyzed.
        operator : str
            Current operator being analyzed.
        analyst_sol : str
            Action chosen by the operator for ticket treatment.
        action_dur : float
            Duration of the action chosen by the operator for ticket treatment.
        steps_dur : list
            List of duration of each action-step taken for ticket treatment.

        Returns
        -------
        None.

        """

        if subfamily not in self.subfamily_analysts_action.keys():
            self.subfamily_analysts_action[subfamily] = {}

        if team not in self.subfamily_analysts_action[subfamily].keys():
            self.subfamily_analysts_action[subfamily][team] = {}

        if operator not in self.subfamily_analysts_action[subfamily][team].keys():
            self.subfamily_analysts_action[subfamily][team][operator] = {}
    
        Utils.update_data(self.subfamily_analysts_action[subfamily][team][operator], action = analyst_sol, duration = action_dur, steps_dur = steps_dur)

    def pick_analyst(self, ticket, analysts_available, mode):
        """
        Searches for the operator to treat the ticket according to the selected mode.

        Parameters
        ----------
        ticket : dict
            Comprises information about the current ticket.
        analysts_available : list
            List of the available operators for ticket treatment.
        mode : int
            0 - Find first free operator; else - find next fastest operator.
            
        Returns
        -------
        analyst : str
            Operator found for ticket treatment.
        analyst_data : dict
            Comprises information about the operator found for ticket treatment.

        """
        team = ticket["team"]
        subfamily = ticket["subfamily"]
    
        if mode == 0:
            analyst = self.find_free_analyst(ticket, analysts_available)
        else:
            analyst = self.find_next_fastest_analyst(ticket, analysts_available)

        analyst_data = {}
        analyst_data[analyst] = {}
        
        analyst_data[analyst]["action"] = list(self.subfamily_analysts_action[subfamily][team][analyst]["action"])
        analyst_data[analyst]["duration"] = float(self.subfamily_analysts_action[subfamily][team][analyst]["duration"])
        Utils.debug_and_log_data(self.aux_data.debug, self.aux_data.logger, f'Analyst: {analyst}, data: {analyst_data[analyst]}')
        
        return analyst, analyst_data

    def find_free_analyst(self, ticket, team_analysts):
        """
        Searches the first available operator.

        Parameters
        ----------
        ticket : dict
            Comprises information about the current ticket.
        team_analysts : list
            List of the available operators for ticket treatment.
            
        Returns
        -------
        analyst : str
            First free operator found for ticket treatment.

        """
        analyst = None
        # This prevents from assigning always the same operator
        temp = random.sample(team_analysts, len(team_analysts))
        analyst = random.choice(temp)
        return analyst

    def find_next_fastest_analyst(self, ticket, analysts_available):
        """
        Searches the next fastest operator.

        Parameters
        ----------
        ticket : dict
            Comprises information about the current ticket.
        team_analysts : list
            List of the available operators for ticket treatment.
            
        Returns
        -------
        operator : str
            First free operator found for ticket treatment.

        """
        
        free_operators = []
        team = ticket["team"]
        subfamily = ticket["subfamily"]

        for x in analysts_available:
            if not self.analysts_info[team]["analysts"][x]["queue"]:
                free_operators.append(x)

        if len(free_operators) == 1:
            return free_operators[0]
        else:
            operator = None
            time = 0
            for i in self.analysts_info[team]["analysts"]:
                if i in free_operators:
                    time_spent = 0
                    if subfamily in self.analysts_info[team]["analysts"][i]["summary"].keys():
                        time_spent = self.analysts_info[team]["analysts"][i]["summary"][subfamily]["Time spent"]
                        
                    if ticket['outlier']:
                        action_dur = self.subfamily_analysts_action[subfamily][team][i]['duration'] + self.aux_data.outlier_cost * self.subfamily_analysts_action[subfamily][team][i]['duration']
                    else:
                        action_dur = self.subfamily_analysts_action[subfamily][team][i]['duration']

                    time_temp = time_spent + action_dur

                    if time == 0:
                        time = time_temp
                        operator = i
                    elif time_temp < time:
                        time = time_temp
                        operator = i
            if self.analysts_info[team]["analysts"][operator]["queue"]:
                Utils.debug_and_log_data(self.aux_data.debug, self.aux_data.logger, f'{operator} is occupied until {self.analysts_info[team]["analysts"][operator]["queue"][-1]}')
                operator = None

            return operator

    def update_ticket_duration(self, ticket):
        """
        Updates the ticket duration based on the existence of outliers.

        Parameters
        ----------
        ticket : dict
            Ticket being analyzed.

        Returns
        -------
        None.

        """
        
        if ticket['outlier']:
            ticket['duration_outlier'] = ticket["duration"] + self.aux_data.outlier_cost * ticket["duration"]
        else:
            ticket['duration_outlier'] = ticket["duration"]
            
    def update_analyst_summary(self, ticket):
        """
        Updates the summary of each operator-subfamily treatment.

        Parameters
        ----------
        ticket : dict
            Ticket being analyzed.

        Returns
        -------
        None.

        """
        
        team = ticket["team"]
        analyst = ticket["analyst"]
        subfamily = ticket["subfamily"]

        if subfamily not in self.analysts_info[team]["analysts"][analyst]["summary"].keys():
            self.analysts_info[team]["analysts"][analyst]["summary"][subfamily] = {}
            Utils.update_data(self.analysts_info[team]["analysts"][analyst]["summary"][subfamily], occurences = 1, time_spent = ticket['duration'], average = ticket['duration'])
        else:
            self.analysts_info[team]["analysts"][analyst]["summary"][subfamily]["occurences"] += 1
            self.analysts_info[team]["analysts"][analyst]["summary"][subfamily]["time_spent"] += ticket['duration']
            self.analysts_info[team]["analysts"][analyst]["summary"][subfamily]["average"] = self.analysts_info[team]["analysts"][analyst]["summary"][subfamily]["time_spent"] / self.analysts_info[team]["analysts"][analyst]["summary"][subfamily]["occurences"]


    ######################## Analyst Operations ########################

    def improve_skill(self, ticket, analysts_info, subfamily_steps_speeds):
        """
        Improves the skill of operators based on a specific counter

        Parameters
        ----------
        ticket : dict
            Ticket being analyzed.
        analysts_info : dict
            Comprises all data about teams and their operators.
        subfamily_steps_speeds : dict
            Comprises all data the steps taken by operators during treatment (steps have data regarding learning rate, speed, among other features).            

        Returns
        -------
        None.

        """

        action = ticket["action"]
        subfamily = ticket["subfamily"]
        curr_date = ticket["allocated_tsp"]
        team = ticket["team"]
        analyst = ticket["analyst"]

        for step in action:
            if subfamily_steps_speeds[subfamily][team][analyst][step]["curr_counter"] == subfamily_steps_speeds[subfamily][team][analyst][step]["max_counter"]:
                Utils.debug_and_log_data(self.aux_data.debug, self.aux_data.logger, f'Improve skill of {analyst} on step {step}')
                subfamily_steps_speeds[subfamily][team][analyst][step]["last_incident"] = curr_date
                learning_rate, speed_updated = Utils.update_step_speed(subfamily_steps_speeds[subfamily][team][analyst], step, analysts_info[team]["analysts"][analyst]["growth"], "improve")
                if speed_updated > 0.2:
                    target_speed = subfamily_steps_speeds[subfamily][team][analyst][step]["target_speed"]
                    if speed_updated > target_speed:
                        Utils.debug_and_log_data(self.aux_data.debug, self.aux_data.logger, f'Updated speed {speed_updated}, learning rate updated: {learning_rate}')
                        subfamily_steps_speeds[subfamily][team][analyst][step]["learning_rate"] = learning_rate
                        subfamily_steps_speeds[subfamily][team][analyst][step]["speed"] = speed_updated
                        subfamily_steps_speeds[subfamily][team][analyst][step]["curr_counter"] = 0
                    else:
                        Utils.debug_and_log_data(self.aux_data.debug, self.aux_data.logger, f'{analyst} already reached speed intended!')
                else:
                    Utils.debug_and_log_data(self.aux_data.debug, self.aux_data.logger, f'{step} cannot be improved anymore!')

    def lose_skill(self, ticket, analysts_info, subfamily_steps_speeds):
        """
        Deteriorates the skill of operators based on time passed

        Parameters
        ----------
        ticket : dict
            Ticket being analyzed.
        analysts_info : dict
            Comprises all data about teams and their operators.
        subfamily_steps_speeds : dict
            Comprises all data the steps taken by operators during treatment (steps have data regarding learning rate, speed, among other features).            

        Returns
        -------
        None.

        """
        subfamily = ticket["subfamily"]
        curr_date = ticket["allocated_tsp"]
        team = ticket["team"]
        analyst = ticket["analyst"]
        action = ticket["action"]

        # 1440 min -> 1 day
        for step in subfamily_steps_speeds[subfamily][team][analyst]:
            if subfamily_steps_speeds[subfamily][team][analyst][step]["last_incident"] != -1 and step not in action:
                time_diff = Utils.calculate_timestamp_diff(subfamily_steps_speeds[subfamily][team][analyst][step]["last_incident"], curr_date, "minutes")
                if time_diff > 10080:  # 1 week
                    Utils.debug_and_log_data(self.aux_data.debug, self.aux_data.logger, "More than 1 week has passed")
                    subfamily_steps_speeds[subfamily][team][analyst][step]["last_incident"] = curr_date
                    if subfamily_steps_speeds[subfamily][team][analyst][step]["speed"] < 1.98:
                        Utils.debug_and_log_data(self.aux_data.debug, self.aux_data.logger, f'{analyst} lost skill on step {step}')
                        learning_rate, speed_updated = Utils.update_step_speed(subfamily_steps_speeds[subfamily][team][analyst], step, analysts_info[team]["analysts"][analyst]["growth"], "worsen")
                        if speed_updated < 2:
                            Utils.debug_and_log_data(self.aux_data.debug, self.aux_data.logger, f'Updated speed {speed_updated}, learning rate updated: {learning_rate}')
                            subfamily_steps_speeds[subfamily][team][analyst][step]["learning_rate"] = learning_rate
                            subfamily_steps_speeds[subfamily][team][analyst][step]["speed"] = speed_updated
                            subfamily_steps_speeds[subfamily][team][analyst][step]["curr_counter"] = 0
                        else:
                            Utils.debug_and_log_data(self.aux_data.debug, self.aux_data.logger, f'{analyst} step cannot be slower')

    def update_analysts_skill(self, ticket, analysts_info, subfamily_steps_speeds):
        """
        Updates the skill of operators

        Parameters
        ----------
        ticket : dict
            Ticket being analyzed.
        analysts_info : dict
            Comprises all data about teams and their operators.
        subfamily_steps_speeds : dict
            Comprises all data the steps taken by operators during treatment (steps have data regarding learning rate, speed, among other features).            

        Returns
        -------
        None.

        """
        self.improve_skill(ticket, analysts_info, subfamily_steps_speeds)
        self.lose_skill(ticket, analysts_info, subfamily_steps_speeds)