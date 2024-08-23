from Code.Utils import Utils, UtilsParams, BufferedRandomChoiceGenerator
from Code.Configurator import Configurator

import pandas as pd
from collections import OrderedDict
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np
import string, random, sys, pytz

class DistributionData:
    # Initiates data about incidents distribution
    def __init__(self, ticket_seasonality_selector, ticket_seasonality, fam_seasonality_selector, fam_seasonality, family_day_time, week_time, distribution_mode, time_equal_probs, week_equal_probs):
        
        self.family_time_probability_pool, self.family_week_probability_pool, self.family_month_probability_pool = {}, {}, {}
        self.ticket_seasonality_selector = ticket_seasonality_selector
        self.ticket_seasonality = ticket_seasonality
        self.family_seasonality_selector = fam_seasonality_selector
        self.family_seasonality = fam_seasonality
        self.family_time_4h = family_day_time
        self.week_time = week_time
        self.distribution_mode = distribution_mode
        self.time_equal_probabilities = time_equal_probs
        self.week_equal_probabilities = week_equal_probs
        
class SuspiciousData:
    # Initiates data about suspicious activity
    def __init__(self, suspicious_countries, suspicious_subfamily, min_coordinated_attack, max_coordinated_attack, min_coordinated_attack_minutes, max_coordinated_attack_minutes, suspicious_ips):
        
        self.suspicious_countries = suspicious_countries
        self.suspicious_subfamily = suspicious_subfamily
        self.min_coordinated_attack = min_coordinated_attack
        self.max_coordinated_attack = max_coordinated_attack
        self.min_coordinated_attack_minutes = min_coordinated_attack_minutes
        self.max_coordinated_attack_minutes = max_coordinated_attack_minutes
        self.suspicious_ips = suspicious_ips

class TicketGenerator:
    # Initiates essential dictionaries and other relevenat params for ticket generation
    def __init__(self, gen_id, domain, generation_params, logger, logger_active):
        
        self._id = gen_id
        self.train_tickets, self.test_tickets, self.clients_info, self.family_steps_pool, self.subfamily_pool = {}, {}, {}, {}, {}
        
        self.n_train_tickets = generation_params["train_ticket"]
        self.n_test_tickets = generation_params["test_ticket"]
        self.ticket_growth_type = generation_params["ticket_growth_type"]
        self.ticket_growth_rate = generation_params["ticket_growth_rate"]
        self.start_date = generation_params["start_date"]
        self.end_date = generation_params["end_date"]
        self.test_timerange = generation_params["test_timerange"]
        self.clients_number = generation_params["clients_number"]
          
        self.family_selection = generation_params["family_selection"]
        self.use_default_family = generation_params["use_default_family"]
        self.family_number = generation_params['families_number']
        self.family_pool = generation_params["default_alert_pool"]
        self.escalate_rate_percentage = generation_params["escalate_rate_percentage"]
        self.techniques_number = generation_params["techniques_number"]
       
        self.minsubfamilies_number = generation_params['minsubfamilies_number']
        self.maxsubfamilies_number = generation_params['maxsubfamilies_number']
        self.min_subtechniques_number = generation_params['minsubtechniques_number']
        self.max_subtechniques_number = generation_params['maxsubtechniques_number']
        self.min_subtechnique_cost = generation_params["min_subtechnique_cost"]
        self.max_subtechnique_cost = generation_params["max_subtechnique_cost"]
        self.min_subtechnique_rate = generation_params["min_subtechnique_rate"]
        self.max_subtechnique_rate = generation_params["max_subtechnique_rate"]
        self.new_family_rate = generation_params["family_rate_percentage"]
        self.new_subfamily_rate = generation_params["subfamily_rate_percentage"]
        self.analysts_info = generation_params["analysts_skills"]
        self.ips_pool = generation_params["ips_pool"]
        self.ip_selected_idx = generation_params["ip_selected_idx"]
        self.special_steps = generation_params["special_steps"]
        
        self.prioritize_lower_teams = generation_params["prioritize_lower_teams"]
        self.teams_frequency = generation_params["teams_frequency"]
        self.family_mean_duration = generation_params["family_mean_duration"]
        
        self.techniques_seasonality_selector = generation_params["techniques_seasonality_selector"]
        self.ip_selector = generation_params["ip_selector"]
        self.ticket_escalation_selector = generation_params["ticket_escalation_selector"]
        
        self.suspicious_data = SuspiciousData(generation_params["suspicious_countries"], generation_params["suspicious_subfamily"], generation_params["min_coordinated_attack"], generation_params["max_coordinated_attack"], generation_params["min_coordinated_attack_minutes"], generation_params["max_coordinated_attack_minutes"], generation_params["suspicious_ips"])
        self.distribution_data = DistributionData(generation_params["ticket_seasonality_selector"], generation_params["ticket_seasonality"], generation_params["family_seasonality_selector"], generation_params["family_seasonality"], generation_params["family_time_4h"], generation_params["week_time"], generation_params["distribution_mode"], generation_params["time_equal_probabilities"], generation_params["week_equal_probabilities"])
        self.aux_data = UtilsParams(generation_params["outlier_rate"], generation_params["outlier_cost"], generation_params["action_operations"], generation_params["max_priority_levels"], generation_params["debug"], logger, logger_active)
        
    # Generates the pool of families to reduce the execution time
    def get_families_probabilities(self, thread_canceled, family_mapping, weight, max_features):

        Utils.debug_and_log_data(self.aux_data.debug, self.aux_data.logger_active, self.aux_data.logger, "\nGet Families Probabilities")
        alert_pool = {}

        if self.family_selection == "Random":
            Utils.debug_and_log_data(self.aux_data.debug, self.aux_data.logger_active, self.aux_data.logger, "Using Random Family Selection")
            if family_mapping != None:
                families_selected = Utils.get_first_n_elements(family_mapping, self.family_number)
            else:
                #print("Family pool:", self.family_pool)
                families_selected = Utils.get_first_n_elements(self.family_pool, self.family_number)
            print("families selected:", families_selected)
        else:
            Utils.debug_and_log_data(self.aux_data.debug, self.aux_data.logger_active, self.aux_data.logger, "Using Customized Family Selection")
            families_selected = self.family_selection.split(" - ")
            print(families_selected)

        if self.use_default_family:
            Utils.debug_and_log_data(self.aux_data.debug, self.aux_data.logger_active, self.aux_data.logger, "Using Default families")
            for fam in families_selected:
                alert_pool[fam] = {}
                Utils.copy_dict(alert_pool[fam], self.family_pool[fam])
                if self.distribution_data.family_seasonality_selector:
                    alert_pool[fam]["real_family"] = families_selected[fam]

                alert_pool[fam]["extra_features"] = []
                n_extra_features = random.randint(0, max_features)
                selected_features = random.sample(range(max_features), n_extra_features)

                for i in selected_features:
                    feature_id = f'_feature_{i}'
                    alert_pool[fam]["extra_features"].append(feature_id)
                if self.ip_selector:
                    # The chance of a family having an associated IP is 30% (chosen by me)
                    alert_pool[fam]["ip"] = np.random.choice([True, False], p=[0.3, 0.7])
        else:
            Utils.debug_and_log_data(self.aux_data.debug, self.aux_data.logger_active, self.aux_data.logger, "Using New Families")
            for fam in families_selected:
                if not thread_canceled:
                    if fam not in alert_pool.keys():
                        print("Family", fam)
                        subfamily_number = random.randint(self.minsubfamilies_number, self.maxsubfamilies_number)
                        Utils.instantiate_family(alert_pool, fam, subfamily_number, max_features, self.distribution_data, self.aux_data, self.ip_selector)
                        if self.distribution_data.family_seasonality_selector:
                            alert_pool[fam]["real_family"] = families_selected[fam]

        # The families probabilities are assigned in intervals of 5 minutes
        time_slots = (60/5) * 24
        for k in alert_pool.keys():
            if not thread_canceled:
                Utils.assign_family_probabilities(k, alert_pool, time_slots, self.distribution_data)

        self.family_pool = alert_pool
        #print("Alert pool:", alert_pool)
        
    # Calculates the difference between similar ticket (time in min)
    def get_last_appearance_time(self, curr_ticket, first_ticket):

        last_occurence = ""
        curr_ticket_time = self.train_tickets[curr_ticket]['raised']
        first_ticket_time = self.train_tickets[first_ticket]['raised']
        time_diff = curr_ticket_time - first_ticket_time

        minutes = round(time_diff.total_seconds() / 60)
        last_occurence = f'The same problem happened {minutes} minutes ago'
        return last_occurence

    # Get clients
    def get_clients(self, lower_bound, upper_bound, size, prefix):
    
        random_integers = np.random.randint(lower_bound, upper_bound + 1, size=size)
        random_integers_with_strings = [f"{prefix}{integer}" for integer in random_integers]
        return random_integers_with_strings

    # Generates sets of subtechniques for each technique used in the family
    def process_step(self, team, family, step, sub_techniques_range, intermediary_techniques_dur, locked):
        
        sub_techniques_num = random.randint(sub_techniques_range[0], sub_techniques_range[1])
        #print("Subtechniques number", sub_techniques_num)
        build_subtechniques = True

        if step in locked:
            if step in self.special_steps["init_opt"].keys():
                act_type = "init_opt"
                #print("In main init")
            elif step in self.special_steps["end_opt"].keys():
                act_type = "end_opt"
                #print("In main end")
            else:
                act_type = "transfer_opt"

            if bool(self.special_steps[act_type][step]):
                if act_type == "transfer_opt":
                    self.family_steps_pool[team][family]["transfer_opt"][step] = self.special_steps[act_type][step]
                else:
                    self.family_steps_pool[team][family][step] = self.special_steps[act_type][step]
                build_subtechniques = False
        else:
            #print(f'Step {step} is not locked')
            self.family_steps_pool[team][family][step] = {}
            
        Utils.debug_and_log_data(self.aux_data.debug, self.aux_data.logger_active, self.aux_data.logger, f'Step {step} is not locked')

        if build_subtechniques:
            sub_techniques = []
            #print("Subtechnques num", sub_techniques_num)
            if self.techniques_seasonality_selector:
                intermediary_subtechniques_dur = Utils.split_steps_dur(intermediary_techniques_dur[step], sub_techniques_num)
            
            for i in range(sub_techniques_num):
                int_technique = random.randint(0, 255)
                # This will break for negative values -> consider[3:]
                hex_technique = hex(int_technique)[2:]
                #print("sub_techniques state", sub_techniques)
                #print("New technique", hex_technique)
                locked_techniques_pool = sub_techniques + locked

                while str(hex_technique) in locked_techniques_pool:
                    Utils.debug_and_log_data(self.aux_data.debug, self.aux_data.logger_active, self.aux_data.logger, f'The technique {hex_technique} already exists. Try another')
                    int_technique = random.randint(0, 255)
                    hex_technique = hex(int_technique)[2:]

                sub_techniques.append(hex_technique)

                if self.techniques_seasonality_selector:
                    step_cost = intermediary_subtechniques_dur[i]
                    self.family_steps_pool[team][family][step][hex_technique] = step_cost
                    Utils.debug_and_log_data(self.aux_data.debug, self.aux_data.logger_active, self.aux_data.logger, f'Step {step} - Subtechnique accepted {hex_technique} with dur {step_cost}')
                else:
                    step_cost = random.randint(self.min_subtechnique_cost, self.max_subtechnique_cost)
                    multiplier = random.randint(self.min_subtechnique_rate, self.max_subtechnique_rate)
                    step_multiplied = int(step_cost * multiplier/100)
                    self.family_steps_pool[team][family][step][hex_technique] = step_multiplied
                    Utils.debug_and_log_data(self.aux_data.debug, self.aux_data.logger_active, self.aux_data.logger, f'Step {step} - Multiplier: {multiplier}. Multiplier Converted: {step_multiplied}')

            Utils.debug_and_log_data(self.aux_data.debug, self.aux_data.logger_active, self.aux_data.logger, f'The step {step} has the following techniques: {self.family_steps_pool[team][family][step]}')

    # Based on probabilities, each technique is assigned a set of subtechniques
    def process_action(self, family, action, sub_techniques_range, intermediary_main_steps, locked_techniques):

        if self.techniques_seasonality_selector:
            locked_duration_steps = Utils.get_locked_techniques_duration(self.special_steps)
            Utils.debug_and_log_data(self.aux_data.debug, self.aux_data.logger_active, self.aux_data.logger, f'With techniques seasonality. lock techniques total dur: {locked_duration_steps}')

        for team in list(self.analysts_info.keys()):    
            if team not in self.family_steps_pool:
                self.family_steps_pool[team] = {}
            self.family_steps_pool[team][family] = {}
            self.family_steps_pool[team][family]["transfer_opt"] = {}
            self.family_steps_pool[team][family]["other_steps"] = {}
            intermediary_techniques_dur = []
            
            if self.techniques_seasonality_selector:
                print("Simulated fam:", family)
                real_family = self.family_pool[family]["real_family"]
                print("Real family:", real_family)
                real_family_duration = round(self.family_mean_duration[real_family])
                if locked_duration_steps < real_family_duration:
                    print("Locked techniques are below mean family")
                    real_family_duration -= locked_duration_steps
                intermediary_techniques_dur = Utils.split_actions_dur(real_family_duration, intermediary_main_steps, sub_techniques_range[1])
                Utils.debug_and_log_data(self.aux_data.debug, self.aux_data.logger_active, self.aux_data.logger, f'Real family: {real_family} - Mean duration: {real_family_duration}\nSubtechniques range: {sub_techniques_range}, Intermediary techniques duration: {intermediary_techniques_dur}')
            
            for step in action:
                Utils.debug_and_log_data(self.aux_data.debug, self.aux_data.logger_active, self.aux_data.logger, f'Step {step} is being analysed')
                if step not in self.family_steps_pool[team][family].keys(): 
                    self.process_step(team, family, step, sub_techniques_range, intermediary_techniques_dur, locked_techniques)

    # Generates a random string with specific length
    def build_action(self, family, length, sub_techniques_range, locked_techniques):

        techniques_pool = string.ascii_letters + string.digits
        init_technique_chosen = random.choice(list(self.special_steps["init_opt"].keys()))
        end_technique_chosen = random.choice(list(self.special_steps["end_opt"].keys()))

        if length > 1:
            techniques_selected = random.sample([tec for tec in techniques_pool if tec not in locked_techniques], k=(self.techniques_number-2))
        else:
            Utils.debug_and_log_data(self.aux_data.debug, self.aux_data.logger_active, self.aux_data.logger, "Length less than 2!")
            techniques_selected = random.sample([tec for tec in string.ascii_letters if tec not in locked_techniques], k=(self.techniques_number-2))
        
        Utils.debug_and_log_data(self.aux_data.debug, self.aux_data.logger_active, self.aux_data.logger, f'Techniques num: {self.techniques_number}, Techniques selected: {techniques_selected}. First technique: {init_technique_chosen}, End technique: {end_technique_chosen}, Length: {length}')

        action_result = str(init_technique_chosen)
        middle_actions = []
        if length > self.techniques_number:
            middle_actions = random.choices(techniques_selected, k=(length-2))
            Utils.debug_and_log_data(self.aux_data.debug, self.aux_data.logger_active, self.aux_data.logger, "Repeated steps included since length is greater than the number of techniques available") 
        else:
            middle_actions = random.sample(techniques_selected, k=(length-2))

        #print("Middle Actions:", middle_actions)
        action_result += ''.join(middle_actions)
        action_result = f'{action_result}{end_technique_chosen}'
        #print("Action result:", action_result)

        Utils.debug_and_log_data(self.aux_data.debug, self.aux_data.logger_active, self.aux_data.logger, f'The family {family} has the action: {action_result}') 
        self.process_action(family, action_result, sub_techniques_range, middle_actions, locked_techniques)

        return action_result

    # Fills the family actions and if they are important for outside hours analysis
    def build_family_action(self, family, sub_techniques_range, locked_techniques):

        # print("Techniques number", techniques_num)
        if self.techniques_number < 10:
            # We assumed that if the number of techniques is < 10, each family should have between 3-5 techniques
            length_min = random.randint(3, 4)
            length_max = random.randint(4, 5)
        else:
            # We assumed that if the number of techniques is > 10, each family should have between 2-8 techniques
            length_min = random.randint(3, 5)
            length_max = random.randint(6, 8)

        length = random.randint(length_min, length_max)
        #print("Length:", length)
    
        action = self.build_action(family, length, sub_techniques_range, locked_techniques)
        self.family_pool[family]["action"] = action

        Utils.debug_and_log_data(self.aux_data.debug, self.aux_data.logger_active, self.aux_data.logger, "Action of each family assigned") 

    # Main action generator
    def generate_actions(self, thread_canceled, weight, dataset_type, with_real):

        Utils.debug_and_log_data(self.aux_data.debug, self.aux_data.logger_active, self.aux_data.logger, f'\nGenerate actions for {dataset_type} dataset') 

        first_team = list(self.analysts_info.keys())[0]
        if dataset_type == "train":
            dataset = self.train_tickets[first_team]
            Utils.split_subfamilies_for_each_team(self.subfamily_pool, self.prioritize_lower_teams, self.teams_frequency)
        else:
            dataset = self.test_tickets[first_team]
            
        locked_techniques = Utils.get_locked_techniques(self.special_steps)
        Utils.debug_and_log_data(self.aux_data.debug, self.aux_data.logger_active, self.aux_data.logger, f'Locked techniques: {locked_techniques}') 

        for i in dataset.keys():
            Utils.debug_and_log_data(self.aux_data.debug, self.aux_data.logger_active, self.aux_data.logger, f'Ticket id: {i}') 
            subfamily = dataset[i]["subfamily"]            
            dataset[i]['team'] = self.subfamily_pool[subfamily]["assigned team"]
            if dataset[i]['team'] == list(self.teams_frequency.keys())[-1]:
                if 'escalate' in dataset[i]:
                    dataset[i]['escalate'] = False
                    
            if with_real:
                sub_techniques_range = []
                sub_techniques_range.append(self.min_subtechniques_number)
                sub_techniques_range.append(self.max_subtechniques_number)
                self.build_family_subfamily_actions(dataset[i]["family"], subfamily, sub_techniques_range, locked_techniques)

        Utils.debug_and_log_data(self.aux_data.debug, self.aux_data.logger_active, self.aux_data.logger, f'All actions generated for the families and subfamilies of {dataset_type} tickets') 

    # Checks if a subfamily has an already allocated. If not it generates a new one
    def build_family_subfamily_actions(self, family, subfamily, sub_techniques_range, locked_techniques):

        if "action" not in self.family_pool[family].keys():
            Utils.debug_and_log_data(self.aux_data.debug, self.aux_data.logger_active, self.aux_data.logger, f'Family {family} does not have an action') 
            self.build_family_action(family, sub_techniques_range, locked_techniques)
        else:
            Utils.debug_and_log_data(self.aux_data.debug, self.aux_data.logger_active, self.aux_data.logger, f'Family {family} action already exists') 

        if subfamily in self.subfamily_pool:
            if self.subfamily_pool[subfamily]['teams_actions']:
                Utils.debug_and_log_data(self.aux_data.debug, self.aux_data.logger_active, self.aux_data.logger, f'Sub actions for teams on {subfamily} already exists')
            else:
                Utils.debug_and_log_data(self.aux_data.debug, self.aux_data.logger_active, self.aux_data.logger, f'Sub actions for teams on {subfamily} does not exist')
                Utils.build_subfamily_action_teams(self.analysts_info, family, subfamily, self.family_pool, self.family_steps_pool, self.subfamily_pool, self.aux_data)

    # Gets the timestamps of each action step
    def get_timestamps(self, step_transitions, allocated_timestamp, outlier):

        transition_dates = []
        if outlier:
            step_transitions= Utils.update_step_outlier(step_transitions, self.aux_data.outlier_cost)

        transition_dates.append(allocated_timestamp)

        for i in step_transitions:
            allocated_timestamp= allocated_timestamp + i * 60
            transition_dates.append(allocated_timestamp)

        #print("Transition dates:", transition_dates)
        return transition_dates

    # Outputs the train dataset
    def output_train_dataset(self, thread_canceled, weight, format_idx, dataset_params, actions_similarity, family_mapping, show_plots, family_subtechniques):

        Utils.debug_and_log_data(self.aux_data.debug, self.aux_data.logger_active, self.aux_data.logger, "Train Ticket Analysis")
        extra_feat = Utils.get_extra_features_used(self.family_pool)

        ticket_ids, ticket_priority, ticket_int_priority, ticket_prioritized, ticket_escalate, clients= [], [], [], [], [], []
        similar_tickets, coord_tickets, ticket_inherited_elapsed_time= [], [], []
        locations, locations_time, location_utc_date, location_utc_timestamp= [], [], [], []
        ticket_unfixed_time, ticket_unfixed_time_timestamp, ticket_timestamps, ticket_fixed_time= [], [], [], []
        alert_family, family_actions, alert_subfamily, subfamily_actions, alert_subfamily_duration= [], [], [], [], []
        ticket_teams, ticket_teams_users, analysts_actions, analyst_actions_status, analyst_action_duration, analyst_action_duration_outlier= [], [], [], [], [], []
        analysts_available, analysts_chosen, analyst_chosen_action, analyst_action_status= [], [], [], []
        ticket_duration, ticket_status, ticket_suspicious, alert_outliers= [], [], [], []
        alert_shifted, user_shifts, = [], []
        
        ip_data_features = ["source_ip", "source_port", "destination_ip", "destination_port"]

        wait_times, resolution_times, ticket_dates = [], [], []
        tickets_summary, priorities_wait_time = {}, {}

        #for i in tickets_fixed.keys():
        for i in self.train_tickets.keys():
            #print("Ticket id:", i)
            ticket= self.train_tickets[i]
            country= ticket['country']
            action= ticket['action']
            family= ticket['family']
            subfamily= ticket['subfamily']
            user= ticket['analyst']
            team= ticket['team']
            client= ticket['client']
            dur= ticket['duration']
            
            subfamily_dur, transitions= Utils.get_action_duration(family, self.subfamily_pool[subfamily]["teams_actions"][team], team, None, None, self.family_steps_pool, family_subtechniques, self.aux_data)

            replicated= False
            if "replicated" in ticket.keys():
                replicated= True

            ticket_ids.append(i)
            alert_family.append(family)
            family_actions.append(self.family_pool[family]["action"])
            alert_subfamily.append(subfamily)
            subfamily_actions.append(self.subfamily_pool[subfamily]["teams_actions"][team])
            ticket_teams.append(team)
            ticket_status.append(ticket["status"])
            ticket_priority.append(ticket["priority"])
            ticket_int_priority.append(self.family_pool[family]["priority"])
            analyst_chosen_action.append(action)
            location_utc_date.append(ticket['raised'])
            ticket_unfixed_time.append(ticket['allocated'])
            ticket_fixed_time.append(ticket['fixed'])
            analysts_chosen.append(user)
            analyst_action_duration.append(dur)
            analyst_action_duration_outlier.append(ticket['duration_outlier'])
            
            wait_time = Utils.calculate_timestamp_diff(ticket['raised_tsp'], ticket['allocated_tsp'], "minutes")
            if self.family_pool[family]["priority"] not in priorities_wait_time:
                priorities_wait_time[self.family_pool[family]["priority"]] = {}
            
            priorities_wait_time[self.family_pool[family]["priority"]][ticket["raised"]] = wait_time
            ticket_dates.append(ticket['raised'].date())

            if "subfamily action duration" in dataset_params and dataset_params["subfamily action duration"]:
                alert_subfamily_duration.append(subfamily_dur)
            if "team analysts" in dataset_params and dataset_params["team analysts"]:
                ticket_teams_users.append(list(self.analysts_info[team]["analysts"].keys()))
            if "analyst actions status" in dataset_params and dataset_params["analyst actions status"]:
                analyst_actions_status.append(ticket["solutions status"])
            if "available analysts" in dataset_params and dataset_params["available analysts"]:
                analysts_available.append(str(ticket["analysts available"])[1:-1])
            if "escalate" in dataset_params and dataset_params["escalate"]:
                ticket_escalate.append(ticket["escalate"])
            if "country" in dataset_params and dataset_params["country"]:
                locations.append(country)
            if "client" in dataset_params and dataset_params["client"]:
                clients.append(client)
            if "wait time" in dataset_params and dataset_params["wait time"]:
                ticket_duration.append(wait_time)
            if "analyst shift" in dataset_params and dataset_params["analyst shift"]:
                user_shifts.append(self.analysts_info[team]["analysts"][user]["shift"])
            if "suspicious" in dataset_params and dataset_params["suspicious"]:
                ticket_suspicious.append(ticket["suspicious"])
            if "stages" in dataset_params and dataset_params["stages"]:
                ticket_timestamps.append(self.get_timestamps(ticket['steps_transitions'], ticket["allocated_tsp"], ticket['outlier']))
            if "raised_tsp" in dataset_params and dataset_params["raised_tsp"]:
                location_utc_timestamp.append(ticket["raised_tsp"])
            if "allocated_tsp" in dataset_params and dataset_params["allocated_tsp"]:
                ticket_unfixed_time_timestamp.append(ticket["allocated_tsp"])
            
            #print("Ticket:", ticket["extra_features"])
            for feature in extra_feat:
                #print("Feature:", feature)
                if feature in ip_data_features:
                    if feature in ticket:
                        #print("Ticket has ip")
                        extra_feat[feature].append(ticket[feature])
                    else:
                        extra_feat[feature].append("---")
                else:
                    if feature in ticket["extra_features"]:
                        extra_feat[feature].append(True)
                    else:
                        extra_feat[feature].append(False)

            if replicated:
                similar= f'Replicated from ticket {ticket["replicated"]}'
                similar_tickets.append(similar)
                ticket_inherited_elapsed_time.append("---")
                if "coordinated" in dataset_params and dataset_params["coordinated"]:
                    coord_tickets.append("---")
            else:
                if ticket["similar"]:
                    #print("i", ticket)
                    similar_tickets.append(ticket["similar_ids"])
                    ticket_inherited_elapsed_time.append(self.get_last_appearance_time(i, ticket["similar_ids"][-1]))
                else:
                    similar_tickets.append("---")
                    ticket_inherited_elapsed_time.append("--")
# =============================================================================
#                 if "coordinated" in dataset_params and dataset_params["coordinated"]:
#                     if ticket["coordinated"] != "---":
#                         # print("i", i)
#                         coord_tickets.append(ticket["coordinated"])
#                     else:
#                         coord_tickets.append("---")
# =============================================================================

            if ticket["status"] == "Transfer":
                if ticket['escalate']:
                    if replicated:
                        analyst_action_status.append("Action updated due to ESCALATION Status")
                    else:
                        analyst_action_status.append("Last step removed due to ESCALATION Status")
                else:
                    if ticket["replication_status"] == "Verification":
                        analyst_action_status.append(f'Distance GREATER than {actions_similarity}')
                    else:
                        analyst_action_status.append("Max similarity reached")
            else:
                analyst_action_status.append(f'Distance LESS {actions_similarity}')

            if ticket['outlier']:
                alert_outliers.append(True)
            else:
                alert_outliers.append(False)
                
            if team not in tickets_summary:
                tickets_summary[team] = {}
                tickets_summary[team]["shifts"] = {}
                tickets_summary[team]["scheduled"] = {}
                tickets_summary[team]["scheduled"]["other_day"] = 0
                tickets_summary[team]["scheduled"]["other_shift"] = 0
                tickets_summary[team]["scheduled"]["others"] = 0
                tickets_summary[team]["prioritized"] = 0
                
            resolution_times.append(ticket['duration_outlier'])

            allocated_shift = Utils.get_ticket_shift(ticket['allocated'].time())    
            if allocated_shift not in tickets_summary[team]["shifts"]:
                tickets_summary[team]["shifts"][allocated_shift] = {}
                
            tickets_summary[team]["shifts"][allocated_shift][i] = {}
            tickets_summary[team]["shifts"][allocated_shift][i]["time_spent"] = dur
            tickets_summary[team]["shifts"][allocated_shift][i]["wait_time"] = wait_time

            wait_times.append(wait_time)
            tickets_summary[team]["shifts"][allocated_shift][i]["analyst"] = user
            tickets_summary[team]["shifts"][allocated_shift][i]["family"] = family
            tickets_summary[team]["shifts"][allocated_shift][i]["subfamily"] = subfamily
            
            if ticket['raised'] != ticket['allocated']:
                if ticket['raised'].day != ticket['allocated'].day:
                    tickets_summary[team]["scheduled"]["other_day"] += 1
                elif Utils.get_ticket_shift(ticket['raised'].time()) != Utils.get_ticket_shift(ticket['allocated'].time()):
                    tickets_summary[team]["scheduled"]["other_shift"] += 1
                else:
                    tickets_summary[team]["scheduled"]["others"] += 1
                
        data = {'id': ticket_ids, 'country': locations, 'country time':locations_time,    
                'raised': location_utc_date, 'raised_tsp': location_utc_timestamp,
                'allocated': ticket_unfixed_time, 'allocated_tsp': ticket_unfixed_time_timestamp, 
                'stages': ticket_timestamps, 'fixed': ticket_fixed_time, 'wait time': ticket_duration,
                'init_priority': ticket_int_priority, 'priority': ticket_priority, 'prioritized': ticket_prioritized, 'client': clients,
                'family': alert_family, 'family action': family_actions, 'subfamily': alert_subfamily, 
                'subfamily action': subfamily_actions, 'subfamily action duration': alert_subfamily_duration, 
                'team': ticket_teams, 'team analysts': ticket_teams_users, 'analysts available': analysts_available, 
                'analysts actions': analysts_actions, 'analysts actions status': analyst_actions_status,
                'analyst': analysts_chosen, 'analyst shift': user_shifts,
                'action': analyst_chosen_action, 'action status': analyst_action_status,
                'duration': analyst_action_duration, 'duration_outlier': analyst_action_duration_outlier,
                # 'Action Chosen No Speed': analyst_action_duration_no_speed, 'coordinated': coord_tickets, 
                'similar': similar_tickets,
                'inheritance elapsed time': ticket_inherited_elapsed_time, 
                'status': ticket_status,
                'escalate': ticket_escalate, 'suspicious': ticket_suspicious,
                'outlier': alert_outliers, 'shifted': alert_shifted}

        output_path = f'trainDataset_{self._id}'

        dataset = Utils.format_generation_datasets(data, output_path, format_idx, dataset_params, extra_feat)
        #Utils.check_dataframe_sorted(dataset)
        Utils.debug_and_log_data(self.aux_data.debug, self.aux_data.logger_active, self.aux_data.logger, "Train Tickets outputted")
        
        self.plot_daily_distribution(dataset)
        self.plot_weekly_distribution(dataset)
        self.plot_monthly_distribution(dataset)
        Utils.plot_dataset_distribution(ticket_dates)
        #Utils.plot_wait_times(ticket_duration, location_utc_date, plot_title)
        #Utils.plot_wait_times_by_init_priority(priorities_wait_time)
        
        #self.evaluate_generation(tickets_summary)
        self.get_tickets_shifted_wait_time(tickets_summary, len(self.train_tickets), wait_times, resolution_times, dataset)

    # # Outputs the test dataset
    def output_test_dataset(self, thread_canceled, weight, format_idx, status):

        Utils.debug_and_log_data(self.aux_data.debug, self.aux_data.logger_active, self.aux_data.logger, "Test Tickets analysis")
        extra_feat = Utils.get_extra_features_used(self.family_pool)

        ticket_ids, ticket_priority, ticket_int_priority, clients = [], [], [], []
        locations, location_utc_date, location_utc_timestamp = [], [], []
        ticket_unfixed_time, ticket_unfixed_time_timestamp, ticket_fixed_time = [], [], []
        alert_family, alert_subfamily, analysts_chosen, analyst_chosen_action = [], [], [], []
        ticket_teams, analyst_action_duration, analyst_action_duration_outlier = [], [], []
        ticket_status, replicated, escalated, tickets_duration = [], [], [], []
        
        ip_data_features = ["source_ip", "source_port", "destination_ip", "destination_port"]

        first_team = list(self.analysts_info.keys())[0]
        if status == "unsolved":
            tickets = self.test_tickets[first_team]
        else:
            tickets = self.test_tickets
            
        for i in tickets:
            #print("id", i)
            if status == "unsolved":
                ticket = self.test_tickets[first_team][i]
            else:
                ticket = self.test_tickets[i]
                
            country = ticket['country']
            family = ticket['family']
            subfamily = ticket['subfamily']
            
            ticket_int_priority.append(self.family_pool[family]["priority"])
            if "new_subfamily" in ticket:
                subfamily = "---"
            elif "new_family" in ticket:
                family = "---"
                subfamily = "---"    
                
            client = ticket['client']
            ticket_ids.append(i)
            locations.append(country)
            location_utc_date.append(ticket['raised'])
            location_utc_timestamp.append(ticket['raised_tsp'])
            ticket_unfixed_time.append(ticket['allocated'])
            ticket_unfixed_time_timestamp.append(ticket['allocated_tsp'])
            clients.append(client)
            ticket_priority.append(ticket["priority"])
            alert_family.append(family)
            alert_subfamily.append(subfamily)

            if status == "unsolved":
                ticket_teams.append("---")
                ticket_status.append("---")
                ticket_fixed_time.append("---")
                analysts_chosen.append("---")
                analyst_chosen_action.append("---")
                analyst_action_duration.append("---")
                analyst_action_duration_outlier.append("---")
                replicated.append("---")
            else:
                ticket_teams.append(ticket['team'])
                ticket_status.append(ticket["status"])
                ticket_fixed_time.append(ticket['fixed'])
                analyst_chosen_action.append(ticket["action"])
                analysts_chosen.append(ticket['analyst'])
                analyst_action_duration.append(ticket['duration'])
                analyst_action_duration_outlier.append(ticket['duration_outlier'])
                if "replicated" in ticket.keys():
                    similar = f'Replicated from ticket {ticket["replicated"]}'
                    replicated.append(similar)
                else:
                    replicated.append("---")
                    
            if ticket['escalate']:
                escalated.append(True)
            else:
                escalated.append(False)

            for feature in extra_feat:
                if feature in ip_data_features:
                    if feature in ticket:
                        extra_feat[feature].append(ticket[feature])
                    else:
                        extra_feat[feature].append("---")
                else:
                    if feature in ticket["extra_features"]:
                        extra_feat[feature].append(True)
                    else:
                        extra_feat[feature].append(False)
                                             
            wait_time = round(Utils.calculate_timestamp_diff(ticket['raised_tsp'], ticket['allocated_tsp'], "minutes"))
            tickets_duration.append(wait_time)

        data = {'id': ticket_ids, 'country': locations, 
                'raised': location_utc_date, 'raised_tsp': location_utc_timestamp,
                'allocated': ticket_unfixed_time, 'allocated_tsp': ticket_unfixed_time_timestamp,
                'fixed': ticket_fixed_time, 'init_priority': ticket_int_priority, 
                'priority': ticket_priority, 'client': clients, 'family': alert_family,
                'subfamily': alert_subfamily, 'team': ticket_teams,
                'analyst': analysts_chosen, 'action': analyst_chosen_action,
                'duration': analyst_action_duration, 'duration_outlier': analyst_action_duration_outlier,
                'status': ticket_status, 'escalate': escalated, 'replicated': replicated}

        output_path = f'testDataset_{status}_{self._id}'
        dataset = Utils.format_generation_datasets(data, output_path, format_idx, None, extra_feat)
        
        if status == "complete":
            Utils.plot_wait_times(tickets_duration, location_utc_date)
          
    # Plots monthly ticket distribution
    def plot_monthly_distribution(self, dataset):
        
        dataset['raised'] = pd.to_datetime(dataset['raised'])
        dataset['month'] = dataset['raised'].dt.month
        day_counts = dataset['month'].value_counts().sort_index()

        # Plot the variation
        plt.figure(figsize=(10, 6))
        day_counts.plot(kind='bar', color='skyblue')
        plt.title('Number of tickets')
        plt.xlabel('Month')
        plt.ylabel('Count')
        plt.xticks(rotation=45)
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        plt.tight_layout()
        plt.show()  
    
    # Plots weekly ticket distribution
    def plot_weekly_distribution(self, dataset):
        
        dataset['raised'] = pd.to_datetime(dataset['raised'])
        dataset['day_of_week'] = dataset['raised'].dt.day_name()
        day_counts = dataset['day_of_week'].value_counts().sort_index()

        # Plot the variation
        plt.figure(figsize=(10, 6))
        day_counts.plot(kind='bar', color='skyblue')
        plt.title('Variation of Datetime Values by Day of the Week')
        plt.xlabel('Day of the Week')
        plt.ylabel('Count')
        plt.xticks(rotation=45)
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        plt.tight_layout()
        plt.show()
        
    # Plots daily ticket distribution
    def plot_daily_distribution(self, dataset):
        
        dataset['raised'] = pd.to_datetime(dataset['raised'])
        dataset['hour_of_the_day'] = dataset['raised'].dt.hour
        day_counts = dataset['hour_of_the_day'].value_counts().sort_index()

        # Plot the variation
        plt.figure(figsize=(10, 6))
        day_counts.plot(kind='bar', color='skyblue')
        plt.title('Variation of Datetime Values by Hour')
        plt.xlabel('Hour')
        plt.ylabel('Count')
        plt.xticks(rotation=45)
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        plt.tight_layout()
        plt.show()

    # Generates the tickets with preliminary data
    def generate_tickets(self, thread_canceled, weight, countries, countries_path):
        
        initial_time = datetime.now()
        networks_used = []
        seasons_choices = None
        families_used, families_used["train"], families_used["test"] = {}, {}, {}

        total_tickets = self.n_train_tickets + self.n_test_tickets
        countries_chosen = np.random.choice(countries, size=total_tickets)
        countries_data = Configurator.get_countries_data(countries_path, countries_chosen)
        
        if self.ticket_escalation_selector:
            escalate_choices = BufferedRandomChoiceGenerator([True, False], [self.escalate_rate_percentage/100, 1 - self.escalate_rate_percentage/100], total_tickets)
        else:
            escalate_choices = BufferedRandomChoiceGenerator([True, False], [0, 1], total_tickets)
        #print("Escalate chosen:", escalate_choices)
        
        outlier_choices = BufferedRandomChoiceGenerator([True, False], [self.aux_data.outlier_rate/100, 1 - self.aux_data.outlier_rate/100], total_tickets)
        #print("Outlier chosen:", outlier_chosen)

        dst_port_type = BufferedRandomChoiceGenerator(["well-known", "registered"], [0.5, 0.5], total_tickets)
        clients = self.get_clients(1, self.clients_number, total_tickets, "Client_")
        
        self.distribution_data.ticket_seasonality_selector = Utils.check_datetime_range_selected(self.start_date, self.end_date, self.distribution_data.ticket_seasonality_selector)
        
        if self.distribution_data.ticket_seasonality_selector:
            seasons_choices = BufferedRandomChoiceGenerator(list(self.distribution_data.ticket_seasonality.keys()), [self.distribution_data.ticket_seasonality["high_season"]["prob"], self.distribution_data.ticket_seasonality["off_season"]["prob"]], total_tickets)
        #print("Seasons:", seasons_choices.buffer)
                
        time_slots = Utils.get_time_slots(self.distribution_data.family_time_probability_pool)
        #print("Time slots:", time_slots)
        
        stime = datetime.strptime(self.start_date, '%d-%m-%Y %H:%M:%S')
        stime = stime.replace(tzinfo=pytz.utc)
        print("Start ticket datetime:", stime)
        etime = datetime.strptime(self.end_date, '%d-%m-%Y %H:%M:%S')
        etime = etime.replace(tzinfo=pytz.utc)
        print("End ticket datetime:", etime)
        
        weekday_shifts, weekend_shifts, weekday_probs, time_daylight_shifts, time_night_shifts, time_light_probs, family_time_shifts_probs, family_week_shifts_probs = Utils.get_shift_data(self.distribution_data)
        year_month_probs, cumulative_probs = Utils.calculate_year_month_ticket_probabilities(self.ticket_growth_type, self.ticket_growth_rate, stime.year, etime.year)

        print("Build Training tickets")
        train_sorted, init_test_tsp = self.assign_ticket_preliminary_data(thread_canceled, self.n_train_tickets, stime.timestamp(), etime.timestamp(), countries_chosen, countries_data, seasons_choices, clients, outlier_choices, escalate_choices, networks_used, weekday_probs, time_light_probs, cumulative_probs, "train")
        self.assign_ticket_family_subfamily(self.n_train_tickets, train_sorted, countries_data, dst_port_type, families_used, time_slots, "train")    
        
        end_test_tsp = init_test_tsp + self.test_timerange * 3600
        #print("Min test datetime:", datetime.utcfromtimestamp(init_test_tsp))
        #print("End test datetime:", datetime.utcfromtimestamp(end_test_tsp))
        print("Build Test tickets")
        test_sorted,_ = self.assign_ticket_preliminary_data(thread_canceled, self.n_test_tickets, init_test_tsp, end_test_tsp, countries_chosen, countries_data, seasons_choices, clients, outlier_choices, escalate_choices, networks_used, None, None, None, "test")
        self.assign_ticket_family_subfamily(self.n_test_tickets, test_sorted, countries_data, dst_port_type, families_used, time_slots, "test")
                
        wait_time, curr_time = Utils.get_function_time_spent(initial_time)
        #average_ticket_time = wait_time / total_tickets
        #print("Average Time to generate a ticket:", average_ticket_time, "seconds")
        Utils.debug_and_log_data(self.aux_data.debug, self.aux_data.logger_active, self.aux_data.logger, "All tickets created")
    
    # Assigns preliminary data to new tickets
    def assign_ticket_preliminary_data(self, thread_canceled, n_tickets, stime, etime, countries_chosen, countries_data, seasons_choices, clients, outlier_choices, escalate_choices, networks_used, weekday_probs, time_light_probs, probabilities_dict, dataset_type):
                
        unsorted_tickets = {}
        #min_datetime = datetime.utcfromtimestamp(stime)
        #print("Min timestamp:", stime)
        #max_datetime = datetime.utcfromtimestamp(etime)
        #print("Max timestamp:", etime)

        for i in range(n_tickets):
            if not thread_canceled:
                print("Ticket id", i)
                country = countries_chosen[i]
                #print("Country:", country)
                if dataset_type == "train":
                    if self.distribution_data.ticket_seasonality_selector:
                        if self.distribution_data.time_equal_probabilities:  
                            if self.distribution_data.week_equal_probabilities:
                                timestamp, utc_datetime = Utils.get_country_data(countries_data[country], stime, etime, self.aux_data.debug, self.distribution_data.ticket_seasonality_selector, self.distribution_data.ticket_seasonality[next(seasons_choices.generate())], None, None, probabilities_dict, self.aux_data)
                            else:
                                timestamp, utc_datetime = Utils.get_country_data(countries_data[country], stime, etime, self.aux_data.debug, self.distribution_data.ticket_seasonality_selector, self.distribution_data.ticket_seasonality[next(seasons_choices.generate())], weekday_probs, None, probabilities_dict, self.aux_data)  
                        else:
                            if self.distribution_data.week_equal_probabilities:
                                timestamp, utc_datetime = Utils.get_country_data(countries_data[country], stime, etime, self.aux_data.debug, self.distribution_data.ticket_seasonality_selector, self.distribution_data.ticket_seasonality[next(seasons_choices.generate())], None, time_light_probs, probabilities_dict, self.aux_data)
                            else:
                                timestamp, utc_datetime = Utils.get_country_data(countries_data[country], stime, etime, self.aux_data.debug, self.distribution_data.ticket_seasonality_selector, self.distribution_data.ticket_seasonality[next(seasons_choices.generate())], weekday_probs, time_light_probs, probabilities_dict, self.aux_data)  
                    else:
                        if self.distribution_data.time_equal_probabilities: 
                            if self.distribution_data.week_equal_probabilities:   
                                timestamp, utc_datetime = Utils.get_country_data(countries_data[country], stime, etime, self.aux_data.debug, False, None, None, None, probabilities_dict, self.aux_data)   
                            else:
                                timestamp, utc_datetime = Utils.get_country_data(countries_data[country], stime, etime, self.aux_data.debug, False, None, weekday_probs, None, probabilities_dict, self.aux_data)   
                        else:
                            if self.distribution_data.week_equal_probabilities:   
                                timestamp, utc_datetime = Utils.get_country_data(countries_data[country], stime, etime, self.aux_data.debug, False, None, None, time_light_probs, probabilities_dict, self.aux_data)   
                            else:
                                timestamp, utc_datetime = Utils.get_country_data(countries_data[country], stime, etime, self.aux_data.debug, False, None, weekday_probs, time_light_probs, probabilities_dict, self.aux_data)            
                else:
                    timestamp, utc_datetime = Utils.get_country_data(countries_data[country], stime, etime, self.aux_data.debug, False, None, None, None, None, self.aux_data)
                #print("Utc datetime:", utc_datetime)
                unsorted_tickets[i] = {}
                Utils.update_data(unsorted_tickets[i], raised = utc_datetime, raised_tsp = timestamp, country = country, allocated = utc_datetime, allocated_tsp = timestamp, temp_allocated = utc_datetime, temp_allocated_tsp = timestamp, client = clients[i], team = "", analyst = None, action = None, duration = None, duration_outlier = None, outlier = next(outlier_choices.generate()), similar = [], escalate = next(escalate_choices.generate()))
    
                # Different clients may share the network
                if clients[i] not in self.clients_info.keys():
                    self.clients_info[clients[i]] = {}
    
                if country not in self.clients_info[clients[i]].keys():
                    self.clients_info[clients[i]][country], self.clients_info[clients[i]][country]["ips"] = {}, {}
                    self.clients_info[clients[i]][country]["networks"] = []
    
                network = Utils.get_country_network(countries_data[country]['ips'], networks_used, self.aux_data.debug)
                networks_used.append(network)
                self.clients_info[clients[i]][country]["networks"].append(network)
                
        sorted_dict = OrderedDict(sorted(unsorted_tickets.items(), key=lambda x: x[1]['raised_tsp']))
        last_id = list(sorted_dict.keys())[-1]
        last_tsp = sorted_dict[last_id]["raised_tsp"]

        # For verification purposes
        if not Utils.is_dict_sorted(sorted_dict):
            print("Not sorted")
            sys.exit()
            
        return sorted_dict, last_tsp
    
    # Assigns families and subfamilies to the tickets (family - incident type; subfamily - incident subtype)
    def assign_ticket_family_subfamily(self, n_tickets, ticket_dict, countries_data, dst_port_type, families_used, time_slots, dataset_type):
        
        ordered_tickets = {} 
        keys = list(ticket_dict.keys())
        new_family, new_subfamily = False, False
        
        for l in range(n_tickets):
            ordered_tickets[l] = ticket_dict[keys[l]]
            ordered_tickets[l]["id"] = l
            if dataset_type == "test":
                new_family = random.choices([True, False], [self.new_family_rate/100, 1 - (self.new_family_rate/100)])[0]
                new_subfamily = random.choices([True, False], [self.new_subfamily_rate/100, 1 - (self.new_subfamily_rate/100)])[0]
                self.distribution_data.family_seasonality_selector = False
            
            if self.distribution_data.distribution_mode == "normal":
                Utils.get_family_subfamily(self.family_pool, self.subfamily_pool, self.distribution_data, ordered_tickets[l], self.suspicious_data, self.aux_data.debug, self.ip_selector, new_family, new_subfamily, time_slots, families_used, dataset_type)
            else:
                family = random.choice(list(self.family_pool.keys()))
                ordered_tickets[l]["family"] = family
                ordered_tickets[l]["subfamily"] = f'{family}_{random.randint(1, self.family_pool[family]["subtypes"])}' 
            self.assign_extra_features(ordered_tickets[l], countries_data, dst_port_type)
            
        for team in self.analysts_info.keys():
            if dataset_type == "train":
                self.train_tickets[team] = {}
            else:
                self.test_tickets[team] = {}
            
        first_team = list(self.analysts_info.keys())[0]
        for k in range(len(ordered_tickets)):
            if dataset_type == "train":
                self.train_tickets[first_team][k] = ordered_tickets[k]
            else:
                self.test_tickets[first_team][k] = ordered_tickets[k]
                
    # Assigns extra features to each ticket (priority, suspicious, and others)
    def assign_extra_features(self, ticket, countries, dst_port_type):

        family = ticket["family"]
        subfamily = ticket["subfamily"]

        ticket['suspicious'] = Utils.check_ticket_suspicious(ticket, self.subfamily_pool[subfamily]['suspicious'], self.suspicious_data.suspicious_countries)
        ticket['priority'] = self.family_pool[family]["priority"]
        ticket['extra_features'] = self.family_pool[family]["extra_features"]

        Utils.assign_ticket_ip(self.family_pool[family]["ip"], ticket, self.clients_info, self.suspicious_data.suspicious_ips, self.ips_pool, self.ip_selected_idx, countries, self.aux_data.debug, dst_port_type)
        
    # Gets the wait time of the tickets shifted for later date
    def get_tickets_shifted_wait_time(self, team_analytics, tickets_number, wait_times, resolution_times, dataset):
        
        tickets_shifted = 0
        for team in team_analytics:
            tickets_shifted += team_analytics[team]["scheduled"]["others"]
            tickets_shifted += team_analytics[team]["scheduled"]["other_day"]
            tickets_shifted += team_analytics[team]["scheduled"]["other_shift"]
           
        print("N tickets shifted:", tickets_shifted)
        #print("Dataset size:", tickets_number)
        #print("Percentage of tickets shifted:", tickets_shifted/tickets_number)
        print("Percentage of tickets shifted:", round((tickets_shifted/tickets_number), 2))
        #print("Total Wait time:", sum(wait_times))
        print("Wait time average:", round((sum(wait_times) / len(wait_times)), 2))
        print("Wait time standard deviation:", round(np.std(wait_times), 2))
        print("Resolution time average:", round((sum(resolution_times) / len(resolution_times)), 2))
        print(f'{round((tickets_shifted/tickets_number), 2) *100}, {round((sum(wait_times) / len(wait_times)), 2)}, {round(np.std(wait_times), 2)}, {round((sum(resolution_times) / len(resolution_times)), 2)}')

    # Evaluates the teams performance
    def evaluate_generation(self, teams_analytics):
        
        #print("--- Generation Evaluation ---")
        print("\n-----  Team Evaluation ---")
        for team in teams_analytics:
            print(f'Team {team} has {len(self.analysts_info[team]["analysts"])} analysts')
            print("Its analysts are:", list(self.analysts_info[team]["analysts"].keys()))
            
            shift_performance = {}
            for shift in teams_analytics[team]["shifts"]:
                shift_performance[shift] = {}
                print(f'-- Shift {shift}:')
                print(f'Total number of tickets treated: {len(teams_analytics[team]["shifts"][shift].keys())}')
                print(f'Ticket ids treated: {list(teams_analytics[team]["shifts"][shift].keys())}')

                total_wait_time, total_time_spent = 0,0
                for ticket_id in teams_analytics[team]["shifts"][shift]:
                    total_wait_time += teams_analytics[team]["shifts"][shift][ticket_id]["wait_time"]
                    total_time_spent += teams_analytics[team]["shifts"][shift][ticket_id]["time_spent"]
                
                print("Total amount time spent (in minutes):", total_time_spent)
                print("Average time spent (in minutes):", total_time_spent/len(teams_analytics[team]["shifts"][shift].keys()))
                shift_performance[shift]["n_tickets"] = len(teams_analytics[team]["shifts"][shift].keys())
                shift_performance[shift]["time_spent"] = total_time_spent
                shift_performance[shift]["wait_time"] = total_wait_time
            
            Utils.analyse_shifts_performance(shift_performance, teams_analytics[team]["shifts"], self.analysts_info[team]["analysts"])
            print("Total number of scheduled tickets:", (teams_analytics[team]["scheduled"]["other_day"] + teams_analytics[team]["scheduled"]["other_shift"] + teams_analytics[team]["scheduled"]["others"]))
            print("Total number of scheduled tickets to other day:", teams_analytics[team]["scheduled"]["other_day"])
            print("Total number of scheduled tickets to other shift:", teams_analytics[team]["scheduled"]["other_shift"])
            print("Total number of scheduled tickets later in their shift:", teams_analytics[team]["scheduled"]["others"])
            print("Total number of tickets prioritized:", teams_analytics[team]["prioritized"])
            print("\n")