"""
Created on Tue Dec 15 12:42:45 2020

@author: leonardo Ferreira
@goal: Has several useful functions applied through out SNOOKER and other systems
"""

import psutil, subprocess, datetime, random, re, ast, string, math, sys, os, shutil, itertools, calendar, ipaddress, logging, json, csv, colorsys
from operator import itemgetter
from datetime import timedelta, datetime, time, timezone
from numpy.linalg import norm
from sklearn.preprocessing import LabelEncoder
from statistics import NormalDist
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pytz
from scipy.optimize import nnls
from collections import Counter

class BufferedRandomChoiceGenerator:
    def __init__(self, options, probabilities, buffer_size):
        """
        Initiates a BufferedRandomChoiceGenerator. Usefull for batch random tasks.

        Parameters
        ----------
        options : list
            Options to generate (for example, it could be True or False).
        probabilities : lits
            Probabilities of the options.
        buffer_size : int
            Number of random choices to generate.

        Returns
        -------
        None.

        """
        self.options = options
        self.probabilities = probabilities
        self.buffer_size = buffer_size
        self.index = 0
        self.generate_new_buffer()

    def generate_new_buffer(self):
        """
        Starts a new buffer, using the BufferedRandomChoiceGenerator attributes.

        Returns
        -------
        None.

        """
        self.buffer = np.random.choice(self.options, p = self.probabilities, size=self.buffer_size)
    
    def generate(self):
        """
        BufferedRandomChoiceGenerator main handler.

        Yields
        ------
        choice : list
            Based on the desided size, it generates n choices.

        """
        while True:
            if self.index >= len(self.buffer):
                self.index = 0
                self.generate_new_buffer()
            choice = self.buffer[self.index]
            self.index += 1
            yield choice

class UtilsParams:
    def __init__(self, outlier_rate, outlier_cost, action_operations, priority_levels, debug, logger):
        """
        Initiates UtilsParams class. Useful for storing various attributes relevant for ticket treatment.

        Returns
        -------
        None.

        """
        self.outlier_rate = outlier_rate
        self.outlier_cost = outlier_cost
        self.action_operations = action_operations
        self.priority_levels = priority_levels
        self.debug = debug        
        self.logger = logger  
        
class Utils:
    def instantiate_priority_queues(priority_levels, team_priority_queues):
        """
        Creates the priority queues that will store the pending tickets.

        Parameters
        ----------
        priority_levels : int
            Max priority level.
        team_priority_queues : dict
            Comprises all the pending tickets, organized according to their priority.

        Returns
        -------
        None.

        """
        for priority in range(1, priority_levels + 1):
            team_priority_queues[priority] = {}
            team_priority_queues[priority]["tickets"] = []
    
    def reset_analysts_data(generation_params, shifts, logger):
        """
        Resets all information about the operators in each team.

        Parameters
        ----------
        generation_params : dict
            Comprises all data about parameters related to ticket and team generation.
        shifts : dict
            Comprises information about the work shifts.
        logger : Logger
            Logging module used for recording and debuging.

        Returns
        -------
        analysts_info : dict
            Comprises all data about teams and their operators.
        save_info : dict
            Initial copy of analysts_info (for storage purposes)

        """
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
                    start_date = datetime.utcfromtimestamp(0).replace(tzinfo=pytz.utc)
                    analysts_info[team]["analysts"][member], save_info[team]["analysts"][member] = {}, {}
                    Utils.update_data(analysts_info[team]["analysts"][member], shift = shift_index, growth = growth, assigned_ticket = None, fixed = start_date, fixed_tsp = 0, summary = {}, active = True)
                    Utils.update_data(save_info[team]["analysts"][member], shift = shift_index, growth = growth, active = True)
                    Utils.debug_and_log_data(generation_params["debug"], logger, f'Shifts used: {shifts_picked}')
                else:
                    shifts_picked[analysts_info[team]["analysts"][member]["shift"]] += 1
                    Utils.debug_and_log_data(generation_params["debug"], logger, f'Analyst shift already assigned. Shifts used: {shifts_picked}')
        
            shifts_picked = {}
        return analysts_info, save_info
    
    def pick_shifts(shifts_used, generation_params, shifts_data, logger):
        """
        Assigns a shift to an operator.

        Parameters
        ----------
        shifts_used : list
            Informs about the work shifts already with operators.
        generation_params : dict
            Comprises all data about parameters related to ticket and team generation.
        shifts_data : dict
            Comprises information about the work shifts.
        logger : Logger
            Logging module used for recording and debuging.

        Returns
        -------
        shift_index : int
            Work shift index assigned to the operator.

        """

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
    
    def get_shift_data(distribution_data):
        """
        Gets the probabilities of a ticket occuring during weekday or weekend and during the day or night.

        Parameters
        ----------
        distribution_data : DistributionData
            Comprises information about the distribution of tickets, families, among other temporal data.

        Returns
        -------
        weekday_shifts : list
            WeekDay index.
        weekend_shifts : list
            WeekEnd index.
        weekday_probs : int
            Probability of occcuring during a weekday.
        time_daylight_shifts: list
            Daylight indexes.
        time_night_shifts : list
            Night time indexes.
        time_light_probs : int
            Probability of occcuring during daylight.
        family_time_shifts_probs : list
            list of probabilities during all day time indexes.
        family_week_shifts_probs : list
            list of probabilities during all days of week indexes.

        """
        family_time_shifts = distribution_data.family_time_4h.keys()
        family_time_shifts_probs = []
        family_week_shifts = distribution_data.week_time.keys()
        family_week_shifts_probs = []
        for i in family_time_shifts:
            family_time_shifts_probs.append(distribution_data.family_time_4h[i]['prob'])
            
        for l in family_week_shifts:
            family_week_shifts_probs.append(distribution_data.week_time[l]['prob'])
              

        # Monday, Tuesday, Wednesday, Thrusday and Friday
        weekday_shifts = [0, 1, 2, 3, 4]
        # Satudardy and Sunday
        weekend_shifts = [5, 6]
        weekday_probs = family_week_shifts_probs[0] + family_week_shifts_probs[1] + family_week_shifts_probs[2] + family_week_shifts_probs[3] + family_week_shifts_probs[4]

        # 2: 8h - 11h59, 3: 12h-15h59, 4: 16h-19h59 (defined in the init configuration file)
        time_daylight_shifts = [2, 3, 4]
        # 0: 24h-04h, 1: 4h-7h59, 5: 20h-23h59 (defined in the init configuration file)
        time_night_shifts = [0, 1, 5]
        time_light_probs = family_time_shifts_probs[2] + family_time_shifts_probs[3] + family_time_shifts_probs[4]
        
        return weekday_shifts, weekend_shifts, weekday_probs, time_daylight_shifts, time_night_shifts, time_light_probs, family_time_shifts_probs, family_week_shifts_probs
    
    def instantiate_family(alert_pool, family, subfamilies_number, max_features, distribution_data, aux_data, ip):
        """
        Instantiates information about each family.   

        Parameters
        ----------
        alert_pool : dict
            Comprises data about the families.
        family : str
            Family being analyzed.
        subfamilies_number : int
            Number of subfamilies to build.
        max_features : int
            Maximum features that the family should have.
        distribution_data : DistributionData
            Comprises information about the distribution of tickets, families, among other temporal data.
        aux_data : UtilsParams
            Comprises auxiliar data, including outlier, priority levels, and other features.
        ip : bool
            Has or does not have ip data.

        Returns
        -------
        None.

        """
        weekday_shifts, weekend_shifts, weekday_probs, time_daylight_shifts, time_night_shifts, time_light_probs, family_time_shifts_probs, family_week_shifts_probs = Utils.get_shift_data(distribution_data)
        
        alert_pool[family] = {}
        alert_pool[family]["subtypes"] = subfamilies_number
        alert_pool[family]["priority"] = random.randint(1, aux_data.priority_levels)
        
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
            shift_time_end = shift_time_end.replace(".999999", "")
                            
            hours_init, minutes_init, seconds_init = map(int, shift_time_init.split(':'))
            hours_end, minutes_end, seconds_end = map(int, shift_time_end.split(':'))
            #print("hours_end", hours_end)
            #print("minutes_end", minutes_end)
            #print("seconds_end", seconds_end)
                    
            x = random.uniform(hours_init, hours_end + (minutes_end/60))

            temp = str(x).split('.')
            loc = float(f'{temp[0]}.{temp[1]}')
            alert_pool[family]['time loc'] = loc
            
            Utils.debug_and_log_data(aux_data.debug, aux_data.logger, f'Shift Time init: {shift_time_init}, Shift Time end: {shift_time_end}, Hour start: {hours_init}, Hour end: {hours_end + (minutes_end/60)}, Time loc: {alert_pool[family]["time loc"]}, Week loc: {alert_pool[family]["week loc"]}')
        alert_pool[family]["extra_features"] = []
        n_extra_features = random.randint(0, max_features)
        selected_features = random.sample(range(max_features), n_extra_features)

        for i in selected_features:
            feature_id = f'_feature_{i}'
            alert_pool[family]["extra_features"].append(feature_id)
           
        if ip:
            alert_pool[family]["ip"] = np.random.choice([True, False], p=[0.3, 0.7])

    def assign_family_probabilities(family, alert_pool, n_time_slots, distribution_data):
        """
        Assigns the probability of a family occuring according to their week and time probabilities.      

        Parameters
        ----------
        family : str
            Family being analyzed.
        alert_pool : dict
            Comprises data about the families.
        n_time_slots : int
            Number of 5-minutes time slots.
        distribution_data : DistributionData
            Comprises information about the distribution of tickets, families, among other temporal data.

        Returns
        -------
        None.

        """
        distribution_data.family_week_probability_pool[family], distribution_data.family_time_probability_pool[family] = {}, {}

        if distribution_data.distribution_mode == "normal":
            print(f'Family {family} follows a normal distribution.')
            week_loc = alert_pool[family]['week loc']
            week_dev = alert_pool[family]['week dev']
            time_loc = alert_pool[family]['time loc']
            time_dev = alert_pool[family]['time dev']
        else:
            print(f'Family {family} follows a uniform distribution.')
        
        for day_shift in distribution_data.week_time.keys():
            if distribution_data.distribution_mode == "normal":
                prob_day = NormalDist(mu = week_loc, sigma = week_dev).pdf(day_shift)
                #prob_before_day = NormalDist(mu = week_loc, sigma = week_dev).pdf(day_shift - 7)
                #prob_after_day = NormalDist(mu = week_loc, sigma = week_dev).pdf(day_shift + 7)
                distribution_data.family_week_probability_pool[family][distribution_data.week_time[day_shift]['day']] =  prob_day #+ prob_before_day + prob_after_day 
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
        
            if distribution_data.distribution_mode == "normal":
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
    
    def get_family_subfamily(alert_pool, sub_alert_pool, distribution_data, ticket, suspicious_data, aux_data, ip, time_slots, families_used):
        """
        Gets the family and subfamily of the ticket according to its datetime.

        Parameters
        ----------
        alert_pool : dict
            Comprises data about the families.
        sub_alert_pool : dict
            Comprises data about the subfamilies.
        distribution_data : DistributionData
            Comprises information about the distribution of tickets, families, among other temporal data.
        ticket : dict
            Ticket being analyzed.
        suspicious_data : SuspiciousData
            Comprises information about suspicious countries and Ips, among other features.
        aux_data : UtilsParams
            Comprises auxiliar data, including outlier, priority levels, and other features.
        ip : bool
            Has or does not have ip data.
        time_slots : dict
            Time of the day divided in 5-minutes slots.
        families_used : dict
            Families and subfamilies already analyzed.

        Returns
        -------
        None.

        """
        ticket_time = '{:02d}:{:02d}'.format(ticket['raised'].hour, ticket['raised'].minute)
        curr_time_slot = Utils.get_current_time_slot(time_slots, ticket_time)        

        day = calendar.day_name[ticket['raised'].weekday()]
        month = calendar.month_name[ticket['raised'].month]
            
        family = ""
        ticket_time_probs, ticket_week_probs, ticket_family_probs, family_cumulative = {}, {}, {}, {}

        for k in distribution_data.family_time_probability_pool.keys():
            ticket_time_probs[k] = distribution_data.family_time_probability_pool[k][curr_time_slot]

        for q in distribution_data.family_week_probability_pool.keys():
            ticket_week_probs[q] = distribution_data.family_week_probability_pool[q][day]
                
        if distribution_data.family_seasonality_selector:
            for l in alert_pool.keys():
                month_ticket_seasonality = distribution_data.family_seasonality[month]
                ticket_family_probs[l] = month_ticket_seasonality[alert_pool[l]["real_family"]]
            
        ticket_probs_total = {x: ticket_time_probs.get(x) * ticket_week_probs.get(x) for x in ticket_time_probs}
        if distribution_data.family_seasonality_selector:
            ticket_probs_total = {x: ticket_probs_total.get(x) * ticket_family_probs.get(x) for x in ticket_probs_total}
        
        ticket_probs_sorted = sorted(ticket_probs_total.items(),  key=itemgetter(1))
        ticket_random = random.uniform(0, sum(ticket_probs_total.values()))
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
        subfamily_updated = f'{family}_{subfamily}'  
        Utils.debug_and_log_data(aux_data.debug, aux_data.logger, f'Subfamily updated: {subfamily_updated}')
        
        ticket['family'] = family
        ticket['subfamily'] = subfamily_updated
        
        Utils.update_subfamily_pool(subfamily_updated, sub_alert_pool, suspicious_data)
        
        if family not in families_used:
            families_used[family] = []
            
        if subfamily not in families_used[family]:
            families_used[family].append(subfamily)
         
    def update_subfamily_pool(subfamily_updated, sub_alert_pool, suspicious_data):
        """
        Updates information about a specific subfamily.

        Parameters
        ----------
        subfamily_updated : str
            Subfamily being analyzed.
        sub_alert_pool : dict
            Comprises data about the subfamilies.
        suspicious_data : SuspiciousData
            Comprises information about suspicious countries and Ips, among other features.

        Returns
        -------
        None.

        """
        if subfamily_updated not in sub_alert_pool:
            sub_alert_pool[subfamily_updated] = {}
            sub_alert_pool[subfamily_updated]['teams_actions'] = {}

            sub_alert_pool[subfamily_updated]['suspicious'] = np.random.choice([True, False], p=[suspicious_data.suspicious_subfamily, 1 - suspicious_data.suspicious_subfamily])
            sub_alert_pool[subfamily_updated]['max_counter'] = random.randint(suspicious_data.min_coordinated_attack, suspicious_data.max_coordinated_attack)
            sub_alert_pool[subfamily_updated]['timerange'] = random.randint(suspicious_data.min_coordinated_attack_minutes, suspicious_data.max_coordinated_attack_minutes)

    def get_time_slots(family_time_probability_pool):
        """
        Gets the 5 minutes intervals probabilities of each family.     

        Parameters
        ----------
        family_time_probability_pool : dict
            Comprises the information about the probability of each time slot in each family.

        Returns
        -------
        TYPE
            List of 5-minutes slots.

        """
        for fam in family_time_probability_pool:
            return list(family_time_probability_pool[fam].keys())
        
    def get_current_time_slot(time_slots, curr_time):
        """
        Gets the time slot according the current time.

        Parameters
        ----------
        time_slots : dict
            Time of the day divided in 5-minutes slots.
        curr_time : str
            Ticket time.

        Returns
        -------
        found_slot : str
            Time slot found.

        """
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
        
        return found_slot
    
    def encode_families(families):
        """
        Encodes the families incidents.        

        Parameters
        ----------
        families : list
            Existing families.

        Raises
        ------
        ValueError
            if idx > 26 + 26 * 26.

        Returns
        -------
        name_to_letter : dict
            Encoded families.

        """
        name_to_letter = {}
        available_letters = list(string.ascii_uppercase)

        for idx, name in enumerate(families):
            if available_letters:
                letter = available_letters.pop(0)
            else:
                if idx < 26 + 26 * 26:
                    combinations = itertools.product(string.ascii_uppercase, repeat=2)  # Two-letter combinations (AA, AB, ..., ZZ)
                    for combo in combinations:
                        if "".join(combo) not in name_to_letter.values():
                            letter = "".join(combo)
                            break
                else:
                    raise ValueError("Maximum number of encodings reached.")
            name_to_letter[letter] = name
        
        return name_to_letter
        
    def get_first_n_elements(dictionary, n):
        """
        Gets first n elements from a dictionary.

        Parameters
        ----------
        dictionary : dict
            Dictionary being analuyzed.
        n : int
            Number of the first n elements to pick from the dictionary.

        Returns
        -------
        dict
            Dictionary with the first n elements picked.

        """
        if n > len(list(dictionary.keys())):
            print("The number of families requested surpasses the number of real families. Use only the number of existent families")
        return {key: dictionary[key] for key in list(dictionary)[:n]}
    
    def build_random_family_names(n):
        
        result = []
        for i in range(1, n + 1):
            s = ""
            num = i
            while num > 0:
                num, rem = divmod(num - 1, 26)
                s = chr(65 + rem) + s  # 65 = ASCII for 'A'
            result.append(s)
        return result
    
    def get_extra_features_used(family_pool):
        """
        Gets the extra features used by all families.    

        Parameters
        ----------
        family_pool : dict
            Comprises data about the families.

        Returns
        -------
        extra_feat : dict
            Comprises information about the extra_features used in the families

        """
        extra_feat = {}
        for fam in family_pool:
            if family_pool[fam]["ip"]:        
                extra_feat["source_ip"], extra_feat["source_port"], extra_feat["destination_ip"], extra_feat["destination_port"] = [],[],[],[]
            for feature in family_pool[fam]["extra_features"]:    
                if feature not in extra_feat:
                    extra_feat[feature] = []
        
        extra_feat = dict(sorted(extra_feat.items()))
        return extra_feat
    
    def assign_ticket_ip(with_ip, ticket, clients_info, suspicious_ips, ips_pool, ip_selected_idx, countries, aux_data, dst_port_type):
        """
        Assigns the destination and source IPs and ports to a ticket.  

        Parameters
        ----------
        with_ip : bool
            Has or does not have ip data.
        ticket : dict
            Ticket being analyzed.
        clients_info : dict
            Comprises information about the clients.
        suspicious_ips : list
            List of suspicious IPs.
        ips_pool : dict
            Comprises information about IPs.
        ip_selected_idx : str
            Index of IP selected (IPv4 or IPv6).
        countries : dict
            Comprises information about the selected countries.
        aux_data : UtilsParams
            Comprises auxiliar data, including outlier, priority levels, and other features.
        dst_port_type : BufferedRandomChoiceGenerator
            Can be either well-known or registered.

        Returns
        -------
        None.

        """
        if with_ip:
            source_country = random.choice(list(countries.keys()))
            src_ip, src_port = Utils.get_source_ip_port(source_country, ticket['suspicious'], countries, suspicious_ips, ips_pool, ip_selected_idx)
            dst_ip, dst_port = Utils.get_destination_ip_port(clients_info[ticket["client"]][ticket["country"]]["networks"], aux_data, ips_pool, ip_selected_idx, dst_port_type)
            ticket['source_ip']= src_ip
            ticket['source_port']= src_port
            ticket['destination_ip']= dst_ip
            ticket['destination_port']= dst_port            
    
    def set_extra_features_values(ticket, family_features):
        """
        Sets temporaries features to families (e.g. "Feature_1) to 1 (existent)

        Parameters
        ----------
        ticket : dict
            Ticket being analyzed.
        family_features : list
            List of existing features.

        Returns
        -------
        None.

        """
        for f in family_features:
            if f not in ticket:
                ticket[f] = 1
            
    def check_datetime_range_selected(start_date, end_date, ticket_seasonality_selector):
        """
        Checks if is possible to use ticket seasonality with the datetime range selected.

        Parameters
        ----------
        start_date : str
            First datetime (str) to check.
        end_date : str
            Last datetime (str) to check.
        ticket_seasonality_selector : bool
            If the generation involves the usage of seasonality from the real dataset.

        Returns
        -------
        bool
            If it possible to use ticket seasonality.

        """
        if ticket_seasonality_selector:
            start_date_datetime = datetime.strptime(start_date, '%d-%m-%Y %H:%M:%S').strftime('%Y-%m-%d')
            end_date_datetime = datetime.strptime(end_date, '%d-%m-%Y %H:%M:%S').strftime('%Y-%m-%d')
            
            month_list = pd.date_range(start=start_date_datetime, end=end_date_datetime, freq='MS')
            #print("mONTHS LIST:", month_list)
            month_list = [month.to_pydatetime().month for month in month_list]
            #print("Months list:", month_list)
            if len(month_list) < 12:
                print("Ticket seasonality was canceled because the dates selected don't cover the whole year!")
                return False
            else:
                return True
        return False
    
    def smooth_ticket_distribution_probabilities(daily_probs):
        """
        Applies smooting to the ticket distribution to avoid sudden rises/drops.

        Parameters
        ----------
        daily_probs : dict
            Comprises the daily distribution of the tickets to be generated.

        Returns
        -------
        smoothed_daily_probs : dict
            Smoothed daily distribution of the tickets to be generated.

        """
        sigma = 6
        window_size = 7
        
        df = pd.DataFrame(list(daily_probs.items()), columns=['month_day', 'probability'])
        df['day_index'] = np.arange(len(df))
        smoothed_probs = np.zeros(len(df))
        
        for i, day in enumerate(df['day_index']):
            start_idx = max(0, i - window_size)  
            end_idx = min(len(df), i + window_size + 1)
            
            window_probs = df['probability'][start_idx:end_idx]
            window_day_indices = df['day_index'][start_idx:end_idx]
            
            weights = []
            for other_day in window_day_indices:
                weight = NormalDist(mu=day, sigma=sigma).pdf(other_day)
                weights.append(weight)
            weights = np.array(weights)
    
            weights /= weights.sum()
            smoothed_probs[i] = np.sum(weights * window_probs)

        smoothed_probs /= smoothed_probs.sum()
        df['smoothed_probability'] = smoothed_probs
        
        smoothed_daily_probs = dict(zip(df['month_day'], df['smoothed_probability']))
        #print("Smoothed daily probs:", smoothed_daily_probs)
        return smoothed_daily_probs 
    
    def apply_seasonality_distribution(distribution_data, growth_rate, start_date, end_date):
        """
        Calculates the probability of the tickets considering the growth rate and real seasonality.

        Parameters
        ----------
        distribution_data : DistributionData
            Comprises information about the distribution of tickets, families, among other temporal data.
        growth_rate : float
            Growth rate of the tickets over the generation timeframe.
        start_date : datetime
            Start datetime generation.
        end_date : datetime
            End datetime generation.

        Returns
        -------
        probabilities_dict : dict
            Comprises information about the ticket distribution based on growth rate and real seasonality.

        """
        probabilities_dict = {}
        cumulative_probability, total_months = 0, 0

        #print("Start date:", start_date)     
        #print("End date:", end_date)      
        current_date = start_date
        current_month = current_date.month
        while current_date <= end_date:
            current_date_only = current_date.date()
            
            if current_date.month != current_month:
                current_month = current_date.month  
                total_months += 1
    
            if growth_rate > 0:
                probability = (1 + growth_rate) ** total_months
            elif growth_rate < 1:
                probability = (1 - abs(growth_rate)) ** total_months
            else:
                probability = 1 ** total_months      
    
            if distribution_data.ticket_seasonality_selector:
                seasonality_prob = distribution_data.ticket_seasonality[current_date.strftime('%m-%d')]["prob"]
                probability *= seasonality_prob

            probabilities_dict[current_date_only] = probability
            cumulative_probability += probability
            current_date += pd.Timedelta(days=1)
           
        for date in probabilities_dict.keys():
            probabilities_dict[date] /= cumulative_probability

        return probabilities_dict
    
    def apply_weekly_distribution(distribution_data, daily_probs, n_tickets):
        """
        Calculates the probabilities of the tickets considering the custom week probabilities.

        Parameters
        ----------
        distribution_data : DistributionData
            Comprises information about the distribution of tickets, families, among other temporal data.
        daily_probs : dict
            Comprises information the daily ticket distribution.
        n_tickets : int
            Number of tickets to generate.

        Returns
        -------
        selected_dates : list
            List of generated dates to be assigned to the tickets.

        """
        if distribution_data.week_equal_probabilities:
            print("Same Week probabilities")
        else:
            print("Different week probs:", distribution_data.week_time)
            week_dict = {key: None for key in daily_probs}

            for date in week_dict.keys():
                day_prob = distribution_data.week_time[date.weekday()]["prob"]
                week_dict[date] = round(day_prob, 1)
                
            daily_probs = {key: daily_probs[key] * week_dict[key] for key in daily_probs}
            total = sum(daily_probs.values())
            daily_probs = {key: value / total for key, value in daily_probs.items()}
            
        days = list(daily_probs.keys())
        days_probs = list(daily_probs.values())
        selected_dates = np.random.choice(days, p=days_probs, size=n_tickets)
        return selected_dates
        
    def apply_daytime_distribution(distribution_data, n_tickets):
        """
        Calculates the probabilties of the tickets considering the custom time probabilities

        Parameters
        ----------
        distribution_data : DistributionData
            Comprises information about the distribution of tickets, families, among other temporal data.
        n_tickets : int
            Number of tickets to generate.

        Returns
        -------
        selected_times : list
            List of generated times to be assigned to the tickets.

        """
        selected_times = []
        
        if distribution_data.time_equal_probabilities:
            print("Same Daytime probabilities")
            for t in range(0, n_tickets):
                seconds = random.randint(0, 86399)
                time = Utils.convert_seconds_to_time(seconds)
                selected_times.append(time)
        else:
            print("Different Daytime probabilities")
            seconds_in_day = 86400
            grid = np.arange(0, seconds_in_day, 1)
            
            time_spikes_mean = []
            spikes_data = {v['mu'].replace(':', 'h'): v['std'] for v in distribution_data.day_ticket_spikes.values()}

            for time_mean in spikes_data.keys():
                time = datetime.strptime(time_mean, "%Hh%M").hour * 3600 + datetime.strptime(time_mean, "%Hh%M").minute * 60
                time_spikes_mean.append(time)

            time_spikes_std = list(spikes_data.values())
            pdf = np.zeros_like(grid, dtype=float)
            
            for mu, sigma in zip(time_spikes_mean, time_spikes_std):
                dist = NormalDist(mu, sigma)
                pdf += np.array([dist.pdf(x) for x in grid])
                
            probs = pdf / np.sum(pdf)
            sampled_indices = np.random.choice(len(grid), size=n_tickets, p=probs)
            selected_seconds = grid[sampled_indices]
            for seconds in selected_seconds:
                time = Utils.convert_seconds_to_time(seconds)
                selected_times.append(time)
                
        return selected_times
        
    def convert_seconds_to_time(seconds):
        """
        Converts total seconds to a time object.

        Parameters
        ----------
        seconds : int
            Total seconds.

        Returns
        -------
        time
            Time object.

        """
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        sec = int(seconds % 60)
        return time(h, m, sec)
    
    def build_date(stime, etime, date, time):
        """
        Builds the generated date considering the selected date and time.    

        Parameters
        ----------
        stime : int
            Start datetime in seconds.
        etime : int
            Start datetime in seconds.
        date : date
            Date generated to be combined.
        time : time
            Time generated to be combined.

        Returns
        -------
        generated_date : datetime
            Datetime combined.
        int
            Timestamp combined.

        """
        generated_date = datetime.combine(date, time)
        generated_date = generated_date.replace(tzinfo=timezone.utc)
        return generated_date, generated_date.timestamp()
        
    def plot_wait_times(tickets_duration, dates, title):
        """
        Plots the wait time of the treating the tickets over time.

        Parameters
        ----------
        tickets_duration : list
            List of the time that tickets waited before being allocated to an operator.
        dates : list
            List of datetimes analyzed.
        title : str
            Plot title.

        Returns
        -------
        None.

        """
        fig, ax = plt.subplots(figsize=(80, 20))
        plt.ylim(0, max(tickets_duration))
        ax.plot(dates, tickets_duration, marker='o', linestyle='-')
        #ax.bar(dates, tickets_duration, width=0.2)
        ax.set_xlabel('Date', fontsize='large')
        ax.set_ylabel('Wait Time (Min)')
        ax.set_title(title, fontsize='x-large')
        os.makedirs("Evaluation", exist_ok=True)
        plt.savefig(f'Evaluation/{title}.png', dpi=300, bbox_inches='tight')
        plt.show()
        
    def plot_wait_times_by_init_priority(priorities_wait_time):
        """
        Plots the wait time of the treating the tickets over time in each priority level.

        Parameters
        ----------
        priorities_wait_time : dict
            Wait time spent in each ticket in each priority level.

        Returns
        -------
        None.

        """
        for priority in priorities_wait_time:
            fig, ax = plt.subplots()
            ax.plot(list(priorities_wait_time[priority].keys()), list(priorities_wait_time[priority].values()), marker='o', linestyle='-', color='b')
            ax.set_xlabel('Date')
            ax.set_ylabel('Number of Tickets')
            ax.yaxis.set_major_locator(plt.MaxNLocator(integer=True))
            ax.set_title(f'Priority {priority}')
            plt.show()
         
    def plot_dataset_distribution(ticket_dates):
        """
        Plots the ticket distribution over the time.

        Parameters
        ----------
        ticket_dates : dict
            Comprises information about the tickets treated in each date.

        Returns
        -------
        None.

        """
        date_counts = Counter(ticket_dates)
        fig, ax = plt.subplots(figsize=(100, 20))
        ax.plot(list(date_counts.keys()), list(date_counts.values()), marker='o', linestyle='-', color='b')
        ax.set_xlabel('Date')
        ax.set_ylabel('Number of Tickets')
        ax.set_title("Dataset Generated Distribution")
        ax.yaxis.set_major_locator(plt.MaxNLocator(integer=True))
        plt.show()

    def check_date_between(begin_time, end_time, check_time=None):
        """
        Checks if a datetime is between other two datetimes.

        Parameters
        ----------
        begin_time : datetime
            Start datetime.
        end_time : datetime
            End datetime.
        check_time : datetime, optional
            Datetime to check. The default is None.

        Returns
        -------
        bool
            If it is within or outside range.

        """
        # If check time is not given, default to current UTC time
        check_time = check_time or datetime.utcnow().time()
        if begin_time < end_time:
            return check_time >= begin_time and check_time <= end_time
        else: # crosses midnight
            return check_time >= begin_time or check_time <= end_time   
        
    def get_ticket_shift(curr_time, shifts):
        """
        Gets the shift where the ticket date is located.

        Parameters
        ----------
        curr_time : time
            Time currently being analyzed.
        shifts : dict
            Comprises information about the shifts (start and end times).

        Returns
        -------
        int
            Shift where the time belongs to.

        """
        for shift_name, times in shifts.items():
            if  times["start"] <= curr_time <= times["end"]:
                return shift_name
        return None  
           
    def split_day_shifts(n_shitfs):
        """
        Splits a day into n shifts.

        Parameters
        ----------
        n_shitfs : int
            Number of shifts to be generated.

        Returns
        -------
        shifts : dict
            Comprises information about the shifts generated.

        """
        total_seconds = 24 * 60 * 60  
        part_seconds = total_seconds / n_shitfs
    
        shifts = {}
        shift = 0
        for i in range(n_shitfs):
            start_sec = int(i * part_seconds)
            start_micro = int((i * part_seconds - start_sec) * 1_000_000)
        
            end_sec = int((i + 1) * part_seconds) - 1
            end_micro = 999_999
            
            start_h = start_sec // 3600
            start_m = (start_sec % 3600) // 60
            start_s = start_sec % 60
        
            end_h = end_sec // 3600
            end_m = (end_sec % 3600) // 60
            end_s = end_sec % 60
        
            shifts[shift] = {}
            shifts[shift]["start"] = time(start_h, start_m, start_s, start_micro)
            shifts[shift]["end"] = time(end_h, end_m, end_s, end_micro)
            shift+=1
    
        return shifts
    
    def update_step_outlier(transitions_dur, outlier_cost):
        """
        Updates the duration of a step from the transition steps based on the presence of outliers.

        Parameters
        ----------
        transitions_dur : list
            List of the durations of the steps.
        outlier_cost : float
            Cost of the outlier.

        Returns
        -------
        transitions_dur_updated : list
            Updated list containig the durations of the steps.

        """
        transitions_dur_updated = []
        
        for i in transitions_dur:
            dur_updated = i + outlier_cost * i
            transitions_dur_updated.append(dur_updated)
            
        return transitions_dur_updated
        
    def check_ticket_suspicious(ticket, suspicious, countries):
        """
        Checks if a ticket is suspicious.

        Parameters
        ----------
        ticket : dict
            Ticket being analyzed.
        suspicious : bool
            If the subfamily is signaled as suspicious.
        countries : dict
            Comprises information about the selected countries.

        Returns
        -------
        bool
            If the ticket is suspicious or not.

        """
        if suspicious:
            country = ticket['country']
            if country in countries:
                start_ticket_time = datetime.strptime(countries[country]["widget start date"].text(), "%H:%M:%S.%f").time()
                end_ticket_time = datetime.strptime(countries[country]["widget end date"].text(), "%H:%M:%S.%f").time()
                if Utils.check_date_between(start_ticket_time, end_ticket_time, ticket['raised'].time()):
                    #print("Ticket id suspicious", ticket)
                    return True

        return False
    
    def get_action_duration(family, action, team, user, steps_data, family_steps_pool, family_subtechniques, aux_data):
        """
        Calculates the duration of a certain action and its progression over the steps.

        Parameters
        ----------
        family : str
            Family being analyzed.
        action : str
            Action being analyzed.
        team : str
            Team being analyzed.
        user : str
            Operator being analyzed.
        steps_data : dict
            Comprises information about the steps taken by an operator.
        family_steps_pool : dict
            Comprises data about the techniques and subfamilies for each family treatment.
        family_subtechniques : dict
            Information about all families analyzed by the teams during ticket treatment.
        aux_data : UtilsParams
            Comprises auxiliar data, including outlier, priority levels, and other features.

        Returns
        -------
        int
            Action total duration (in minutes).
        transitions : list
            List of durations of each step taken.

        """
        dur = 0
        transitions = []
        family_techniques = family_steps_pool[team][family]
        action = Utils.change_action_format(action)
        Utils.debug_and_log_data(aux_data.debug, aux_data.logger, f'Calculate action duration of {action}')

        for step in action:
            if step in family_steps_pool[team][family]["transfer_opt"].keys():
                Utils.debug_and_log_data(False, aux_data.logger, "Last step is a transfer operation")
                subtech_dur = family_steps_pool[team][family]["transfer_opt"][step]
            elif step in family_techniques["other_steps"].keys():
                Utils.debug_and_log_data(False, aux_data.logger, "Step comes from other families")
                subtech_dur = family_techniques["other_steps"][step]
            else:
                subtech_dur = family_subtechniques[team][family][step]

            if user != None:  
                Utils.debug_and_log_data(aux_data.debug, aux_data.logger, f'Get duration of step {step} for {user}')
                step_speed = float(steps_data[step]["speed"])
                user_step_dur = Utils.get_user_step_range(subtech_dur, step_speed)
                dur += user_step_dur
                transitions.append(user_step_dur)
            else:
                dur += subtech_dur
                
        Utils.debug_and_log_data(aux_data.debug, aux_data.logger, f'Final duration: {round(dur, 2)}')
        return round(dur, 2), transitions
    
    def get_user_step_range(subtechnique_dur, speed):
        """
        # Gets the duration of an operator-step.

        Parameters
        ----------
        subtechnique_dur : float
            Duration of a subtechnique.
        speed : float
            Speed of the operator.

        Returns
        -------
        float
            Operator-step duration.

        """
        if speed < 1:
            max_step_dur = subtechnique_dur / speed
            min_step_dur = subtechnique_dur * speed
        else:            
            min_step_dur = subtechnique_dur / speed
            max_step_dur = subtechnique_dur * speed
        
        user_step_dur = random.uniform(min_step_dur, max_step_dur)
        return round(user_step_dur, 2)

    def get_action_duration_outlier(action_dur, outlier, outlier_cost):
        """
        Gets the duration of an action with outlier.        

        Parameters
        ----------
        action_dur : float
            Duration of the action.
        outlier : bool
            It it is an outlier or not.
        outlier_cost : float
            Outlier cost.

        Returns
        -------
        action_outlier : float
            Updated action duration with outlier.

        """
        if outlier:
            action_outlier = action_dur + round(action_dur * outlier_cost, 1)
        else:
            action_outlier = action_dur 
            
        return action_outlier
    
    def convert_to_escaleted_action(ticket, action, transfer_data):
        """
        Converts the action into escalated.

        Parameters
        ----------
        ticket : dict
            Ticket being analyzed.
        action : str
            Action being analyzed.
        transfer_data : list
            List with transfer step data.

        Returns
        -------
        list
            Updated action as a list.

        """
        action[-1] = transfer_data[0]
        if len(action) > 2:
            action.pop(len(action) - 2)

        action_updated = ""
        for l in range(len(action)):
            action_updated += "'" + action[l] + "'"
               
        return Utils.change_action_format(action_updated)
    
    def check_close_shift(team_priority_queue, tickets_info, aux_data):
        """
        Checks whether the highest priority level has any pending tickets not analyzed.

        Parameters
        ----------
        team_priority_queue : dict
            Comprises information about the pending tickets within each priority.
        tickets_info : dict
            Comprises information about all tickets.
        aux_data : UtilsParams
            Comprises auxiliar data, including outlier, priority levels, and other features.

        Returns
        -------
        bool
            True - analyze the next new ticket; False - Review the next ticket from the pending tickets.

        """
        
        max_priority = Utils.get_highest_priority_with_tickets(team_priority_queue)
        if max_priority != None:
            highest_priority_ticket_id = team_priority_queue[max_priority]["tickets"][0]
            if "analyzed_in_shift" in tickets_info[highest_priority_ticket_id]:
                Utils.debug_and_log_data(aux_data.debug, aux_data.logger, "Highest priority ticket already analyzed. Closed shift is set to true to review the remaining pending tickets")
                return True
            
        return False
    
    def get_next_ticket(ticket, close_shift, curr_shift, analysts_in_shift, original_dict_idx, tickets, original_keys, analysts_info, priority_queues, families_resolution, shifts_data, aux_data):
        """
        Gets the data of the next ticket to be analyzed (can be from the pending tickets or the pool of unprocessed tickets).    

        Parameters
        ----------
        ticket : dict
            Ticket being analyzed.
        close_shift : bool
            Read from pending tickets (priority queues) or from the unprocessed tickets.
        curr_shift : int
            Shift currently being analyzed.
        analysts_in_shift : list
            Operators working in the current shift.
        original_dict_idx : int
            Index from the unprocessed tickets pool.
        tickets : dict
            Comprises information about all tickets.
        original_keys : list
            Keys from the tickets (without replicated tickets).
        analysts_info : dict
            Comprises all data about teams and their operators.
        priority_queues : dict
            Comprises all the pending tickets, organized according to their priority.
        families_resolution : dict
            Comprises the mean duration spent to treat each family.
        shifts_data : dict
            Comprises information about the work shifts.
        aux_data : UtilsParams
            Comprises auxiliar data, including outlier, priority levels, and other features.

        Returns
        -------
        ñext_id : int
            Next ticket id to read.
        original_dict_idx : int
            Index from the unprocessed tickets pool.
        curr_shift : int
            Next shift to analyze.
        analysts_in_shift : list
            Analysts in the shift analyzed next.

        """
        if Utils.check_tickets_in_team_queue(priority_queues, ticket["team"]):
            next_ticket_id, temp_date, temp_tsp, highest_priority_ticket_id = Utils.get_next_pending_ticket(ticket, analysts_info, analysts_in_shift, priority_queues[ticket["team"]], tickets, close_shift, families_resolution, shifts_data[curr_shift], aux_data)

            update_ticket = True
            if "analyzed_in_shift" in tickets[next_ticket_id]:
                Utils.debug_and_log_data(aux_data.debug, aux_data.logger, f'id {next_ticket_id} was analyzed in shift {curr_shift}')
                update_ticket = False
                
            Utils.debug_and_log_data(aux_data.debug, aux_data.logger, f'Update_ticket: {update_ticket}')

            if original_dict_idx + 1 >= len(original_keys):
                Utils.debug_and_log_data(aux_data.debug, aux_data.logger, f'Original data already read! Next_id {next_ticket_id} - {tickets[next_ticket_id]["allocated"]}')
                
                if update_ticket:
                    tickets[next_ticket_id]["allocated"] = temp_date
                    tickets[next_ticket_id]["allocated_tsp"] = temp_tsp
                    Utils.debug_and_log_data(aux_data.debug, aux_data.logger, f'Test ticket {next_ticket_id} in {temp_date}')
                    return next_ticket_id, original_dict_idx, curr_shift, analysts_in_shift
                else:
                    pending_shift = Utils.get_ticket_shift(temp_date.time(), shifts_data)
                    next_ticket_date, next_shift = Utils.get_next_shift_data(temp_date, pending_shift, shifts_data)   
                    Utils.update_allocated_times(tickets, priority_queues, ticket["team"], next_ticket_date, next_ticket_date.timestamp(), aux_data) 
                    analysts_in_next_shift = Utils.get_operators_in_shift(analysts_info[ticket["team"]], next_shift)
                    Utils.debug_and_log_data(aux_data.debug, aux_data.logger, f'Pending tickets are going to be analyzed in {next_ticket_date} on shift {next_shift} with operators {analysts_in_next_shift}')
                    return next_ticket_id, original_dict_idx, next_shift, analysts_in_next_shift
            else:
                next_original_key = original_keys[original_dict_idx + 1]
                next_original_ticket_date = tickets[next_original_key]["raised"] 
                Utils.debug_and_log_data(aux_data.debug, aux_data.logger, f'Pending date: {temp_date}. Next original ticket: {tickets[next_original_key]["raised"]}')
                
                if temp_date <= next_original_ticket_date:
                    pending_shift = Utils.get_ticket_shift(temp_date.time(), shifts_data)
                    next_original_shift = Utils.get_ticket_shift(next_original_ticket_date.time(), shifts_data)
                    if pending_shift != next_original_shift or (pending_shift == next_original_shift and next_original_ticket_date.day != temp_date.day):
                        if next_ticket_id == highest_priority_ticket_id and not update_ticket:
                            next_ticket_date, next_shift = Utils.get_next_shift_data(temp_date, curr_shift, shifts_data)   
                            Utils.update_allocated_times(tickets, priority_queues, ticket["team"], next_ticket_date, next_ticket_date.timestamp(), aux_data) 
                            analysts_in_next_shift = Utils.get_operators_in_shift(analysts_info[ticket["team"]], next_shift)
                            Utils.debug_and_log_data(aux_data.debug, aux_data.logger, f'Pending tickets are going to be analyzed in {next_ticket_date} on shift {next_shift} with operators {analysts_in_next_shift}')
                            return next_ticket_id, original_dict_idx, next_shift, analysts_in_next_shift

                        tickets[next_ticket_id]["allocated"] = temp_date
                        tickets[next_ticket_id]["allocated_tsp"] = temp_tsp
                        Utils.debug_and_log_data(aux_data.debug, aux_data.logger, f'Test ticket {next_ticket_id} in {temp_date}')
                                
                        if Utils.get_ticket_shift(tickets[next_ticket_id]["allocated"].time(), shifts_data) != curr_shift:
                            next_shift = Utils.get_next_shift(Utils.get_ticket_shift(tickets[next_ticket_id]["allocated"].time(), shifts_data), shifts_data)
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
                            
                            if Utils.get_ticket_shift(tickets[next_ticket_id]["allocated"].time(), shifts_data) != curr_shift:
                                next_shift = Utils.get_next_shift(Utils.get_ticket_shift(tickets[next_ticket_id]["allocated"].time(), shifts_data), shifts_data)
                                Utils.debug_and_log_data(aux_data.debug, aux_data.logger, f'next_shift {next_shift}')
                                analysts_in_next_shift = Utils.get_operators_in_shift(analysts_info[ticket["team"]], next_shift)
                                return next_ticket_id, original_dict_idx, next_shift, analysts_in_next_shift
                            else:
                                return next_ticket_id, original_dict_idx, curr_shift, analysts_in_shift

        if bool(tickets) and original_dict_idx + 1 < len(tickets):
            original_dict_idx += 1
            next_id = original_keys[original_dict_idx]

            if Utils.get_ticket_shift(tickets[next_id]["allocated"].time(), shifts_data) != curr_shift:
                next_shift = Utils.get_ticket_shift(tickets[next_id]["allocated"].time(), shifts_data)
                Utils.debug_and_log_data(aux_data.debug, aux_data.logger, f'next_shift {next_shift}')
                analysts_in_next_shift = Utils.get_operators_in_shift(analysts_info[ticket["team"]], next_shift)
                return next_id, original_dict_idx, next_shift, analysts_in_next_shift
                
            Utils.debug_and_log_data(aux_data.debug, aux_data.logger, f'Ticket id {next_id} is read from original_dict')
        else:
            next_id = None

        return next_id, original_dict_idx, curr_shift, analysts_in_shift
    
    def get_next_pending_ticket(ticket, analysts_info, analysts_in_shift, team_priority_queue, tickets, close_shift, families_resolution, shift_data, aux_data):
        """
        Gets the next pending ticket from replicated and pending tickets.

        Parameters
        ----------
        ticket : dict
            Ticket being analyzed.
        analysts_info : dict
            Comprises all data about teams and their operators.
        analysts_in_shift : list
            Operators working in the current shift.
        team_priority_queue : dict
            Comprises information about the pending tickets within each priority.
        tickets : dict
            Comprises information about all tickets.
        close_shift : bool
            Read from pending tickets (priority queues) or from the unprocessed tickets.
        families_resolution : dict
            Comprises the mean duration spent to treat each family.
        shift_data : dict
           Comprises information about the current work shift.
        aux_data : UtilsParams
            Comprises auxiliar data, including outlier, priority levels, and other features.

        Returns
        -------
        highest_priority_ticket_id : int
            Next ticket id with the highest priority.
        datetime
            Next ticket allocated datetime.
        int
            Next ticket allocated timestamp.
        highest_priority_ticket_id : int
            Same as before (for later verification).

        """
        min_time, min_tsp = None, None
        
        max_priority = Utils.get_highest_priority_with_tickets(team_priority_queue)
        min_time, min_tsp = Utils.find_min_analyst_endtime(analysts_info[ticket["team"]]["analysts"], analysts_in_shift, aux_data)
        highest_priority_ticket_id = team_priority_queue[max_priority]["tickets"][0]
        
        if close_shift:
            Utils.debug_and_log_data(aux_data.debug, aux_data.logger, f'Priority queue {team_priority_queue}. \nTicket date: {ticket["allocated"]}. Min time: {min_time}. Close shift')

            if ticket["id"] == highest_priority_ticket_id:
                Utils.debug_and_log_data(aux_data.debug, aux_data.logger, "Is the highest priority ticket")
            else:
                if ticket["id"] in team_priority_queue[ticket["priority"]]["tickets"]:
                    Utils.debug_and_log_data(aux_data.debug, aux_data.logger, f'Curr ticket id {ticket["id"]} is the ticket with lowest priority')
                else:
                    Utils.debug_and_log_data(aux_data.debug, aux_data.logger, "Curr ticket id was fixed")
                    
            Utils.debug_and_log_data(aux_data.debug, aux_data.logger, "Test with other tickets with lower priority")
            end_datetime = datetime.combine(min_time.date(), shift_data["end"])
            end_datetime_utc = end_datetime.replace(tzinfo=pytz.UTC)
            end_datetime_tsp = end_datetime_utc.timestamp()
            
            remaining_time = Utils.calculate_timestamp_diff(end_datetime_tsp, min_tsp, "minutes")
            Utils.debug_and_log_data(aux_data.debug, aux_data.logger, f'Remaining time until shift ending: {remaining_time}. End datetime: {end_datetime}, Min Time: {min_time}')    
            
            ticket_id_index = 0
            next_ticket_id = Utils.get_next_ticket_id_pending(ticket_id_index, team_priority_queue, max_priority, tickets, families_resolution, remaining_time, aux_data)
            if next_ticket_id != None:
                return next_ticket_id, min_time, min_tsp, highest_priority_ticket_id
            
            next_priority = max_priority - 1
            if next_priority >= min(team_priority_queue): 
                ticket_id_index = 0
                while next_priority >= min(team_priority_queue): 
                    #Utils.debug_and_log_data(aux_data.debug, aux_data.logger, f'Next priority {next_priority}')
                    if team_priority_queue[next_priority]["tickets"]:
                        #Utils.debug_and_log_data(aux_data.debug, aux_data.logger, f'Number of tickets in the next priority {next_priority} is {len(team_priority_queue[next_priority]["tickets"])}')
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

    def get_next_ticket_id_pending(ticket_id_index, team_priority_queue, priority, tickets, families_resolution, remaining_time, aux_data):
        """
        Gets the next ticket id waiting for treatment

        Parameters
        ----------
        ticket_id_index : int
            Ticket id index.
        team_priority_queue : dict
            Comprises information about the pending tickets within each priority.
        priority : int
            Priority level being analyzed.
        tickets : dict
            Comprises information about all tickets.
        families_resolution : dict
            Comprises the mean duration spent to treat each family.
        remaining_time : int
            Time remaining to treat a ticket before the shift ends.
        aux_data : UtilsParams
            Comprises auxiliar data, including outlier, priority levels, and other features.

        Returns
        -------
        temp_ticket_id : int
            Next ticket id to process.

        """
        while True:
            if ticket_id_index < len(team_priority_queue[priority]["tickets"]):
                temp_ticket_id = team_priority_queue[priority]["tickets"][ticket_id_index]
                if "analyzed_in_shift" not in tickets[temp_ticket_id]:
                    if tickets[temp_ticket_id]["family"] in families_resolution:
                        if families_resolution[tickets[temp_ticket_id]["family"]]["avg_time"] < remaining_time:
                            #Utils.debug_and_log_data(aux_data.debug, aux_data.logger, f'Check next id is {temp_ticket_id} from priority {priority}')
                            return temp_ticket_id
                        else:
                            Utils.debug_and_log_data(aux_data.debug, aux_data.logger, f'Next id should not be analyzed now since the average is {families_resolution[tickets[temp_ticket_id]["family"]]["avg_time"]}')
                    else:
                        Utils.debug_and_log_data(aux_data.debug, aux_data.logger, f'Check next id is {temp_ticket_id} from priority {priority}. Not registed in families resolution')
                        return temp_ticket_id
            else:
                break
            ticket_id_index += 1
        return None
        
    def get_highest_priority_with_tickets(team_tickets):
        """
        Gets the highest priority level with pending tickets.

        Parameters
        ----------
        team_tickets : dict
            Comprises information about the pending tickets within each priority in a team.

        Returns
        -------
        priority : int
            Highest priority with pending tickets.

        """
        min_priority = min(team_tickets)
        max_priority = max(team_tickets)

        for priority in range(max_priority, min_priority -1 , -1):
            if team_tickets[priority]["tickets"]:
                return priority
            
        return None

    def get_next_priority(curr_priority, max_priority):
        """
        Gets the next priority considering the current priority.        

        Parameters
        ----------
        curr_priority : int
            Current priority.
        max_priority : int
            Maximum existing priority.

        Returns
        -------
        int
            Next priority level.

        """
        if curr_priority < max_priority:
            return curr_priority + 1
        else:
            return curr_priority
    
    def check_tickets_in_team_queue(priority_queues, team):
        """
        Checks if there are any pending tickets assigned to a particular team

        Parameters
        ----------
        priority_queues : dict
            Comprises all the pending tickets, organized according to their priority.
        team : str
            Team being analyzed.

        Returns
        -------
        bool
            There are or aren't any pending tickets in this team.

        """
        for priority in priority_queues[team]:
            if priority_queues[team][priority]["tickets"]:
                return True
        
        return False
    
    def is_sorted_by_datetime(ticket_list, tickets_info, logger):
        """
        Checks if list of tickets is sorted by datetime.

        Parameters
        ----------
        ticket_list : list
            List of tickets being analyzed.
        tickets_info : dict
            Comprises information about all tickets.
        logger : Logger
            Logging module used for recording and debuging.

        Returns
        -------
        bool
            List of tickets sorted or not.

        """
        for i in range(len(ticket_list) - 1):
            current_id = ticket_list[i]
            current_datetime = tickets_info[current_id]["raised_tsp"]
            next_id = ticket_list[i + 1]
            next_datetime = tickets_info[next_id]["raised_tsp"]
            
            if current_datetime > next_datetime:
                return False
        return True
    
    def build_subfamily_action(team, family, subfamily, action, family_steps_pool, aux_data):
        """
        Builds the subfamily action.    

        Parameters
        ----------
        team : str
            Team being analyzed.
        family : str
            Family being analyzed.
        subfamily : str
            Subfamily being analyzed.
        action : str
            Family action that serves as baseline for subfamily action generation.
        family_steps_pool : dict
            Comprises data about the techniques and subfamilies for each family treatment.
        aux_data : UtilsParams
            Comprises auxiliar data, including outlier, priority levels, and other features.

        Returns
        -------
        updated_action : str
            Subfamily action.

        """
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
    
    def build_analyst_action(family, subfamily, team, operator, action, steps_info, special_tech, aux_data):
        """
        Builds actions for operators.

        Parameters
        ----------
        family : str
            Family being analyzed.
        subfamily : str
            Subfamily being analyzed.
        team : str
            Team being analyzed.
        operator : str
            Operator being analyzed.
        action : str
            Family action used as baseline.
        steps_info : dict
            Comprises information about the steps available to treat an incident in a team.
        special_tech : list
            List containing initiate, end, and transfer actions.
        aux_data : UtilsParams
            Comprises auxiliar data, including outlier, priority levels, and other features.

        Returns
        -------
        subtechniques_cleaned : list
            New operator action.

        """
        subtechniques = action.split("'")
        subtechniques_cleaned = [x for x in subtechniques if x]

        Utils.debug_and_log_data(aux_data.debug, aux_data.logger, f'Generate action for analyst {operator} using the action {subtechniques_cleaned} in subfamily {subfamily}')

        operations_number = random.randint(2, 3)
        operations = random.choices(aux_data.action_operations, (0.85, 0.05, 0.05, 0.05), k = operations_number)
        
        while ('+' or '-' or '%') not in operations:
            operations = random.choices(aux_data.action_operations, (0.85, 0.05, 0.05, 0.05), k = operations_number)

        Utils.debug_and_log_data(aux_data.debug, aux_data.logger,f'Operations: {operations}')
        for opt in operations:      
            #Utils.debug_and_log_data(aux_data.debug, aux_data.logger, f'Operation: {opt}')
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

    def check_shift_ending(ticket_time_complete, action_dur, shifts_data, aux_data):
        """
        Checks if the time that it takes to fix a ticket surpasses the operator shift.

        Parameters
        ----------
        ticket_time_complete : datetime
            Fixed ticket datetime.
        action_dur : float
            Treatment action duration.
        shifts_data : dict
            Comprises information about the work shifts.
        aux_data : UtilsParams
            Comprises auxiliar data, including outlier, priority levels, and other features.

        Returns
        -------
        bool
            If there is a change in the shift or not.

        """
        next_time = ticket_time_complete + timedelta(minutes = action_dur)
        current_shift = Utils.get_ticket_shift(ticket_time_complete.time(), shifts_data)
        next_shift = Utils.get_ticket_shift(next_time.time(), shifts_data)

        if current_shift != next_shift:
            Utils.debug_and_log_data(aux_data.debug, aux_data.logger, "Action will surpass the analyst's shift")
            return True
        else:
            return False
    
    def calculate_with_levenshtein(a,b):
        """
        Calculates the Levenshtein distance between two lists.

        Parameters
        ----------
        a : list
            First list being compared.
        b : list
            Second list being compared.

        Returns
        -------
        int
            Distance between the lists analyzed.

        """
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
    
    def calculate_distance(action_chosen, subfamily_action):
        """
        Calculates similarity between operator and subfamily actions.

        Parameters
        ----------
        action_chosen : list
            Operator Action.
        subfamily_action : str
            Subfamily Action.

        Returns
        -------
        distance : int
            Distance between operator and subfamily actions.

        """
        subfam_action = subfamily_action.split("'")
        subfam_action = [x for x in subfam_action if x]
        
        distance = Utils.calculate_with_levenshtein(action_chosen, subfam_action)
        return distance
           
    def check_ticket_distance(ticket, user_action, subfamily_action, actions_similarity, all_teams, ticket_verification):
        """
        Checks the ticket status.

        Parameters
        ----------
        ticket : dict
            Ticket being analyzed.
        user_action : list
            Operator action.
        subfamily_action : str
            Subfamily Action.
        actions_similarity : int
            Maximum action disparity.
        all_teams : list
            All teams involved in ticket treatment.
        ticket_verification : bool
            If the distance between operator and subfamily actions should be verifiable.

        Returns
        -------
        str
            Assign Closed or Transfer as the ticket status.

        """
        team = ticket["team"]
        distance = Utils.calculate_distance(user_action, subfamily_action)
        ticket["distance"] = distance

        if distance >= actions_similarity and ticket_verification:
            index = all_teams.index(team)
            if index <= 2:
                return "Transfer"
        return "Closed"

    def check_escalated_similar_tickets(ticket_id, tickets_data, tickets_inheritance, ticket_similarity_selector, subfamily_pool, last_team, aux_data):
        """
        Checks if a ticket should be escalated due to initial escalation or max similarity reached.   

        Parameters
        ----------
        ticket_id : int
            Ticket id being analyzed.
        tickets_data : dict
            Comprises information about all tickets.
        tickets_inheritance : dict
            Comprises information about ticket similarity (in terms of client and subfamily).
        ticket_similarity_selector : bool
            Check ticket similarity or not.
        subfamily_pool : dict
            Comprises data about the subfamilies.
        last_team : str
            Last treatment team available.
        aux_data : UtilsParams
            Comprises auxiliar data, including outlier, priority levels, and other features.

        Returns
        -------
        None.

        """
        if tickets_data[ticket_id]["escalate"]:
            if tickets_data[ticket_id]["team"] != last_team:
                tickets_data[ticket_id]["replication_status"] = "Escalation"
                tickets_data[ticket_id]["status"] = "Transfer"
                Utils.debug_and_log_data(aux_data.debug, aux_data.logger, "To replicate due to escalation")
            else:
                Utils.debug_and_log_data(aux_data.debug, aux_data.logger, "Can't be replicated because it is already on the top team")
        else:
            if ticket_similarity_selector and not tickets_data[ticket_id]["similarity_analysis"]:
                Utils.check_similar_coordinated_tickets(tickets_data[ticket_id], tickets_data, tickets_inheritance, subfamily_pool, aux_data)
    
    def check_similar_coordinated_tickets(ticket, tickets_data, tickets_inheritance, subfamily_pool, aux_data):
        """
        Checks for similar tickets.

        Parameters
        ----------
        ticket : dict
            Ticket being analyzed.
        tickets_data : dict
            Comprises information about all tickets.
        tickets_inheritance : dict
            Comprises information about ticket similarity (in terms of client and subfamily).
        subfamily_pool : dict
            Comprises data about the subfamilies.
        aux_data : UtilsParams
            Comprises auxiliar data, including outlier, priority levels, and other features.

        Returns
        -------
        None.

        """
        ticket_id = ticket["id"]
        client= ticket["client"]
        subfamily= ticket["subfamily"]
        datetime_raised= ticket["raised"]
        ticket["similarity_analysis"] = True
        
        ticket["similar"], ticket["coordinated"] = [], []
    
        if client not in tickets_inheritance:
            tickets_inheritance[client] = {}
            
        if subfamily not in tickets_inheritance[client]:
            tickets_inheritance[client][subfamily] = {}
            end_date = datetime_raised + timedelta(minutes = subfamily_pool[subfamily]["timerange"])
            Utils.update_data(tickets_inheritance[client][subfamily], start = datetime_raised, end = end_date, curr_counter = 1)
            tickets_inheritance[client][subfamily]["similar"], tickets_inheritance[client][subfamily]["similar_ids"] = [], []
            tickets_inheritance[client][subfamily]["similar"].append(ticket_id)
            tickets_inheritance[client][subfamily]["similar_ids"].append(ticket_id)
        else:
            if tickets_inheritance[client][subfamily]["start"] <= datetime_raised <= tickets_inheritance[client][subfamily]["end"]:    
                ticket["similar"] = list(tickets_inheritance[client][subfamily]["similar"])
                ticket["similar_ids"] = list(tickets_inheritance[client][subfamily]["similar_ids"])
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
                #print(f'ticket {ticket_id} of {subfamily} will be replicated due to {ticket["replication_status"]}')

    def get_country_network(networks, networks_used, aux_data):
        """
        Generates a random location (country).    

        Parameters
        ----------
        networks : list
            List of networks available.
        networks_used : list
            List of networks already analyzed.
        aux_data : UtilsParams
            Comprises auxiliar data, including outlier, priority levels, and other features.

        Returns
        -------
        random_network : str
            Network picked.

        """
        random_network = random.choice(networks)
        Utils.debug_and_log_data(aux_data.debug, aux_data.logger, "Country of each ticket assigned")
        return random_network

    def get_source_ip_port(country, suspicious, countries, suspicious_ips, ips_pool, ip_selected_idx):
        """
        Generates the IP and Port of a country serving as source.        

        Parameters
        ----------
        country : str
            Country being analyzed.
        suspicious : bool
            If the subfamily is signaled as suspicious.
        countries : dict
            Comprises information about the selected countries.
        suspicious_ips : list
            List of suspicious IPs.
        ips_pool : dict
            Comprises information about IPs.
        ip_selected_idx : str
            Index of IP selected (IPv4 or IPv6).

        Returns
        -------
        random_ip : str
            Source IP.
        src_port : int
            Source port.

        """
        # Port 0-1023 – Well known ports (server services by the Internet)
        # Ports 1024-49151 - Registered Port (semi-served ports)
        # Ports 49152-65535 - free to use by client programs (ephemeral ports)
        # Source in the last
        # Generates the Ports  
    
        if not suspicious:
            ips_network_available = countries[country]["ips"]
            random_network = random.choice(ips_network_available)
            net = ipaddress.IPv4Network(random_network)
            random_ip_index = random.randint(0, net.num_addresses -1)
            random_ip = net[random_ip_index]
        else:
            random_ip = random.choice(list(suspicious_ips))

        src_port = random.randint(49152, 65535)    

        if ips_pool[ip_selected_idx] == "IPv6Address":
            random_ip = ipaddress.IPv6Address(f'2002::{random_ip}').compressed
            print("IP converted to IPv6")
            
        return random_ip, src_port

    # Generates the IP and Port of Destination Country
    def get_destination_ip_port(client_network, aux_data, ips_pool, ip_selected_idx, dst_port_type):
        """
        Generates the IP and Port of a country serving as destination.          

        Parameters
        ----------
        client_network : list
            List of networks available.
        aux_data : UtilsParams
            Comprises auxiliar data, including outlier, priority levels, and other features.
        ips_pool : dict
            Comprises information about IPs.
        ip_selected_idx : str
            Index of IP selected (IPv4 or IPv6).
        dst_port_type : BufferedRandomChoiceGenerator
            Can be either well-known or registered.

        Returns
        -------
        random_ip : str
            Destination IP.
        dst_port : int
            Destination Port.

        """
        random_network = random.choice(client_network)
        net = ipaddress.IPv4Network(random_network)

        random_ip_index = random.randint(0, net.num_addresses -1)
        random_ip = net[random_ip_index]
        Utils.debug_and_log_data(aux_data.debug, aux_data.logger, f'Network {net} has an range of {net.num_addresses}, Ip index: {random_ip_index}')
        
        if ips_pool[ip_selected_idx] == "IPv6Address":
            random_ip = ipaddress.IPv6Address(f'2002::{random_ip}').compressed
            print("IP converted to IPv6")
            
        dst_port_type = next(dst_port_type.generate())

        if dst_port_type == "well-known":
            dst_port = random.randint(0, 1023)
        else:
            dst_port = random.randint(1024, 49151)
        return random_ip, dst_port

    def get_subtechniques(family, steps_pool, step, locked):
        """
        Gets the subtechniques of each step of the family action.

        Parameters
        ----------
        family : str
            Family being analyzed.
        steps_pool : dict
            Comprises data about the techniques and subfamilies of a family.
        step : str
            Action step being analyzed.
        locked : dict
            Contains information about forbidden steps (initiate, end, and transfer).

        Returns
        -------
        subtechniques : list
            List of subtechniques within a family.

        """
        subtechniques = []
        if isinstance(locked, dict):
            locked = Utils.flat_lists(list(locked.values()))

        family_techniques = steps_pool[family]
        
        for i in family_techniques.keys():
            if i not in locked:
                for l in family_techniques[i].keys():
                    if l not in locked:
                        if step != l:
                            subtechniques.append(l)
        
        return subtechniques
        
    def split_subfamilies_for_each_team(subfamilies_pool, first_team):
        """
        Splits the tickets to be treated in different teams.

        Parameters
        ----------
        subfamilies_pool : dict
            Comprises data about the subfamilies.
        first_team : str
            Lowest team.

        Returns
        -------
        None.

        """

        for subfamily in subfamilies_pool:
            subfamilies_pool[subfamily]["assigned team"] = first_team

    def close_excel():
        """
        Closes any excel file opened (prevents output wrinting fail).

        Returns
        -------
        None.

        """
        excel_found = False
        for proc in psutil.process_iter():
            if proc.name() == "EXCEL.EXE": 
                print("Excel instances found!")
                excel_found = True
                subprocess.call(["taskkill", "/f", "/im", "EXCEL.EXE"])            
        if not excel_found:
            print("Excel instances not found!")

    def is_dict_sorted(my_dict):
        """
        Checks if a dictionary is sorted by datetime.

        Parameters
        ----------
        my_dict : dict
            Dictionary being analyzed.

        Returns
        -------
        bool
            True if sorted; False if unsorted.

        """        
        values = list(my_dict.values())
        for i in range(len(values) - 1):
            current_datetime = values[i]['raised']
            next_datetime = values[i + 1]['raised']
            if current_datetime > next_datetime:
                return False
        return True
    
    def format_generation_datasets(data, name, format_idx, dataset_params, extra_feat, plot_title):
        """
        Applies special format to the output file.    

        Parameters
        ----------
        data : dictionary
            Data to be converted into a Dataframe.
        name : str
            Output format.
        format_idx : int
            0 - CSV and 1 - XLSX.
        dataset_params : dict
            Comprises the column features that should be included in the generated datasets.
        extra_feat : dict
            Extra features to be included in the dataframe.
        plot_title : str
            Title of the generated dataset.

        Returns
        -------
        dataset : dataframe
            Dataframe converted from data with different formating.

        """
        extra_feat = {k: v for k,v in extra_feat.items() if v}
        for i in extra_feat:
            data[i] = extra_feat[i]
            data_columns = data.keys()
        
        if "Dataset" in name:
            params = [k for k, v in dataset_params.items() if v == False]
            for item_name in params:
                
                items_columns = [item for item in data_columns if item_name in item]
                for column in items_columns:
                    del data[column]
                    
                    
        dataset = pd.DataFrame(data, columns=list(data.keys()))
        dataset['id'] = dataset['id'].astype('int64')
        dataset['priority'] = dataset['priority'].astype('int8')
        dataset['init_priority'] = dataset['init_priority'].astype('int8')
        
        categorical_columns = ['country', 'client', 'family', 'family', 'subfamily', 'team', 'analyst', 'status']
        for col in categorical_columns:
            dataset[col] = dataset[col].astype('category')

        if "Dataset" in name:    
            dataset['duration'] = dataset['duration'].astype('float32')
            dataset['duration_outlier'] = dataset['duration_outlier'].astype('float32')
            categorical_columns = ['family action', 'subfamily action', 'action status'] #'inheritance elapsed time']
            for col in categorical_columns:
                dataset[col] = dataset[col].astype('category')
    
        if format_idx == 0:
            filename = f'./Output/Generation/{name}.csv'
            dataset.to_csv(filename, encoding='utf-8', index=False, sep=';')
        else:
            if not Utils.check_excel_limit_rows(dataset, name): 
                filename = f'./Output/Generation/{name}_{plot_title}.xlsx'
                writer = pd.ExcelWriter(filename, engine='xlsxwriter')
                dataset.to_excel(writer, sheet_name='Tickets Info', index = False)  
                workbook  = writer.book
                #worksheet = writer.sheets['Tickets Info']   
                format1 = workbook.add_format()
                format1.set_align('center')
    
                #worksheet.set_column(dataset.columns.get_loc("ID"), dataset.columns.get_loc("Time Difference"), 7, format1)
                #worksheet.set_column(dataset.columns.get_loc("Location"), dataset.columns.get_loc("Time Difference"), 18, format1, {'level': 1, 'hidden': True})
                #worksheet.set_column(dataset.columns.get_loc("Ticket Raised (UTC)"), dataset.columns.get_loc("Users Off Days"), 20, format1)
                #worksheet.set_column(dataset.columns.get_loc("Team Users"), dataset.columns.get_loc("Users Next Shift"), 20, format1, {'level': 1, 'hidden': True})
                #worksheet.set_column(dataset.columns.get_loc("Users Available"), dataset.columns.get_loc("Destination PORT"), 20, format1)
                
                writer.save()        
        return dataset
                    
    def check_excel_limit_rows(dataset, name):
        """
        Checks if dataset reach the max rows of Excel.

        Parameters
        ----------
        dataset : dataframe
            Dataframe being analyzed.
        name : str
            Name of the file to be outputed.

        Returns
        -------
        bool
            Does surpass or not Excel limit rows.

        """
        # Excel limit row is 1,048,576 
        if dataset.shape[0] > 104876:
            print("Saved on csv file due to excel limit rows!")
            filename = f'./Output/Generation/{name}.csv'
            dataset.to_csv(filename, encoding='utf-8', index=False, sep=';')
            return True
        else:
            return False
        
    def get_family_middle_subtechniques(family_steps_pool):
        """
        Gets all families subtechniques (excluding locked subtechniques).

        Parameters
        ----------
        family_steps_pool : dict
            Comprises data about the techniques and subfamilies for each family treatment.

        Returns
        -------
        family_subtechniques : dict
            Subtechniques of all families.

        """
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
    
    def get_locked_techniques(special_steps):
        """
        Gets special subtechniques (start, end and transfer)    

        Parameters
        ----------
        special_steps : dict
            Comprises information about special steps.

        Returns
        -------
        locked : dict
            Contains information about forbidden steps (initiate, end, and transfer).

        """
        if not isinstance(special_steps["init_opt"], list): 
            locked = list(special_steps["init_opt"].keys()) + list(special_steps["end_opt"].keys()) + list(special_steps["transfer_opt"].keys())
            for opt in special_steps["init_opt"].values():
                locked+= list(opt.keys())
            for opt in special_steps["end_opt"].values():
                locked+= list(opt.keys())
        else:
            locked = special_steps["init_opt"] + special_steps["end_opt"] + special_steps["transfer_opt"]
        
        return locked
    
    def get_locked_techniques_duration(special_steps, action):
        """
        Gets the duration of special subtechniques (start and end).

        Parameters
        ----------
        special_steps : dict
            Comprises information about special steps.
        action : str
            Action being analyzed.

        Returns
        -------
        total_dur : float
            Total duration of start and end steps

        """
        init_step = action[0]
        last_step = action[-1]
        
        init_operations = list(special_steps["init_opt"][init_step].values())[0]
        end_operations = list(special_steps["end_opt"][last_step].values())[0]
        
        total_dur = 0
        total_dur += init_operations + end_operations
        return total_dur
    
    def reset_generation_folder(path):
        """
        Resets the output folder.

        Parameters
        ----------
        path : str
            Folder to be reset.

        Returns
        -------
        None.

        """
        for filename in os.listdir(path):
            file_path = os.path.join(path, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print('Failed to delete %s. Reason: %s' % (file_path, e))
                
        print(f'All files from {path} were removed')
        
    def is_folder_empty(folder_path):
        """
        Checks if the folder exists and has any file.

        Parameters
        ----------
        folder_path : str
            Folder to be checked.

        Raises
        ------
        ValueError
            if folder is not a directory.

        Returns
        -------
        int
            Has or does not have files in the folder.

        """
        if not os.path.isdir(folder_path):
            raise ValueError(f"The path '{folder_path}' is not a valid directory.")

        return len(os.listdir(folder_path)) == 0
    
    def get_most_recent_file(folder_path):
        """
        Gets the most recent file in a folder.

        Parameters
        ----------
        folder_path : str
            Folder to be checked.

        Raises
        ------
        ValueError
            if folder is empty.

        Returns
        -------
        most_recent_file : str
            Most recent file.

        """
        files = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
   
        if not files:
            raise ValueError(f"The folder '{folder_path}' is empty or contains no files.")

        most_recent_file = max(files, key=os.path.getmtime)
        return most_recent_file
    
    def get_smallest_file(folder_path):
        
        files = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))] 
        smallest_file = min(files, key=os.path.getsize)
        print(f"Smallest file: {os.path.basename(smallest_file)} ({os.path.getsize(smallest_file)} bytes)")
 
        return os.path.basename(smallest_file)
     
    def calculate_timestamp_diff(t1, t2, time_unit):
        """
        Calculates the time different between two timestamps in a certain time unit.

        Parameters
        ----------
        t1 : timestamp
            First timestamp analyzed.
        t2 : timestamp
            Second timestamp analyzed.
        time_unit : str
            Time unit difference.

        Returns
        -------
        float
            Time difference between two timestamps.

        """
        diff_seconds = abs(t2 - t1)
        if time_unit == "seconds":
            return diff_seconds
        elif time_unit == "minutes":
            diff_minutes = diff_seconds / 60
            return round(diff_minutes)
        else:
            diff_hours = diff_seconds / 3600
            return diff_hours
            
    def split_actions_dur(x, techniques):
        """
        Splits a duration according to the number of techniques used in an action (uses real treatment duration).

        Parameters
        ----------
        x : float
            Duration to split.
        techniques : list
            Techniques to assign duration.

        Returns
        -------
        techniques_dur : dict
            Comprises the duration of each newly subtechnique using real data.

        """
        techniques_dur = {}
        n = len(techniques)    
        
        durations = Utils.split_steps_dur(x, n)
        
        for idx in range(len(techniques)):
            techniques_dur[techniques[idx]] = durations[idx]
        
        return techniques_dur
    
    def split_steps_dur(x, n_techniques):
        """
        Splits the duration according to the number of subtechniques.  

        Parameters
        ----------
        x : float
            Duration to split.
        n_techniques : int
            Number of techniques to assign duration.

        Returns
        -------
        durations : list
            List of assigned durations.

        """
        durations = []
        
        if n_techniques == 1:
            durations.append(x)
        else:
            durations = [1] * n_techniques
            remaining = int(x - n_techniques) 
            
            for i in range(remaining):
                durations[i % n_techniques] += 1
            
        return durations
    
    def build_subtechniques_dur(base_dur, n_subtechniques):
        """
        Builds subtechniques duration according to a delta.

        Parameters
        ----------
        base_dur : float
            Baseline duration.
        n_subtechniques : int
            Number of subtechniques to assign duration.

        Returns
        -------
        durations : list
            List of generated duration using the delta obtained.

        """    
        lower_limit = base_dur * 0.9
        upper_limit = base_dur * 1.1
        
        durations = [random.uniform(lower_limit, upper_limit) for _ in range(n_subtechniques)]

        return durations
    
    def change_action_format(action):
        """
        Converts the action format to list.

        Parameters
        ----------
        action : str
            Action for ticket treatment.

        Returns
        -------
        list
            Action in list format.

        """
        
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

    def get_speed(curve, x):
        """
        Gets a new operator speed.

        Parameters
        ----------
        curve : float
            Operator growth.
        x : float
            Learning rate.

        Returns
        -------
        float
            Updated operator speed.

        """
        return round((-math.log(x*curve, 10)+2)/2, 2)

    def update_data(variable, **kwargs):        
        """
        Updates the content of a variable.

        Parameters
        ----------
        variable : can have multiple types
            Variable to be updated.
        **kwargs : can have multiple contents
            Content of the variables to be updated.

        Returns
        -------
        None.

        """
        variable.update(kwargs)
        
    def update_analyst_data(ticket, train_id, teams_data):
        """
        Updates the data pertaining an operator in a team.

        Parameters
        ----------
        ticket : dict
           Ticket being analyzed.
        train_id : int
            Ticket identifier.
        teams_data : dict
            Comprises information about all treatment teams.

        Returns
        -------
        None.

        """
        team = ticket["team"]
        analyst = ticket["analyst"]
        
        Utils.update_data(teams_data[team]["analysts"][analyst], assigned_ticket = ticket["id"], fixed = ticket['fixed'], fixed_tsp = round(ticket["fixed_tsp"], 1))
        teams_data[team]["analysts"][analyst]["summary"][train_id] = ticket["duration_outlier"]

    def replicate_ticket(teams_data, original_ticket, tickets, priority_queues, n_replicated, aux_data):
        """
        Replicates and escalates a ticket to the next team.

        Parameters
        ----------
        teams_data : dict
            Comprises information about all treatment teams.
        original_ticket : dict
            Ticket being analyzed (without replicated).
        tickets : dict
            Comprises information about all tickets.
        priority_queues : dict
            Comprises all the pending tickets, organized according to their priority.
        n_replicated : int
            Number of replicated tickets.
        in_generation : bool
            Whether this task is related to ticket treatment or not (can be applied to other types of operations).
        aux_data : UtilsParams
            Comprises auxiliar data, including outlier, priority levels, and other features.

        Returns
        -------
        n_replicated : int
            Updated number on the replicated tickets.

        """
        team = original_ticket["team"]
        ticket_id = original_ticket["id"]
        all_teams = list(teams_data)
    
        if team != all_teams[-1]:
            n_replicated += 1
            next_team = Utils.get_next_team(team, list(teams_data))

            next_id = len(tickets[next_team])
            tickets[next_team][next_id] = {}
            rep_ticket = tickets[next_team][next_id]
            rep_ticket["id"] = next_id

            Utils.update_data(rep_ticket, raised = original_ticket["fixed"], raised_tsp = original_ticket["fixed_tsp"], allocated = original_ticket["fixed"], allocated_tsp = original_ticket["fixed_tsp"], team = next_team, analyst = "---")
            Utils.update_data(rep_ticket, country = original_ticket["country"], client =  original_ticket["client"], family = original_ticket["family"], subfamily = original_ticket["subfamily"], priority = original_ticket["priority"], outlier = original_ticket["outlier"], replicated = ticket_id, escalate = False, replication_status = None)

            substr = ['feature', 'source', 'destination']
            filtered_features = Utils.filter_string(list(original_ticket.keys()), substr)
            for feature in filtered_features:
                rep_ticket[feature] = original_ticket[feature]

            if "new_family" in original_ticket:
                Utils.update_data(rep_ticket, new_family = original_ticket["new_family"])
                
            if "new_subfamily" in original_ticket:
                Utils.update_data(rep_ticket, new_subfamily = original_ticket["new_subfamily"])
            
            Utils.debug_and_log_data(aux_data.debug, aux_data.logger, f'N replicated_tickets: {n_replicated} in {team}. New ticket was added to upper teams: {priority_queues[next_team][original_ticket["priority"]]["tickets"]}')
        else:
            Utils.debug_and_log_data(aux_data.debug, aux_data.logger, "Can't be replicated because it is already on the top team")
    
        return n_replicated
    
    def get_next_team(curr_team, all_teams):
        """
        Gets the next team considering the current one.

        Parameters
        ----------
        curr_team : str
            Current team being analyzed.
        all_teams : list
            All exiting teams.

        Returns
        -------
        next_team : str
            Next team.

        """
        index = all_teams.index(curr_team)
        next_team = all_teams[index + 1]    
        return next_team
    
    # Get the next teams
    def get_remaining_teams(curr_team, all_teams):
        """
        Gets the remaining teams after a certain team

        Parameters
        ----------
        curr_team : str
            Current team being analyzed.
        all_teams : list
            All exiting teams.

        Returns
        -------
        remaining_teams : list
            Remaining team (wraps around circularly).

        """
        remaining_teams = []
        
        if curr_team in all_teams:
            for team_idx in range(all_teams.index(curr_team) + 1, len(all_teams)):
                next_team = all_teams[team_idx]
                remaining_teams.append(next_team)
            
        return remaining_teams
    
    def get_next_shift(curr_shift, shifts_data):
        """
        Gets the next shift.

        Parameters
        ----------
        curr_shift : int
            Current work shift.
        shifts_data : dict
            Comprises information about the work shifts.

        Returns
        -------
        int
            Next shift index available.

        """
        shifts = list(shifts_data.keys())
        idx = shifts.index(curr_shift)
        next_idx = (idx + 1) % len(shifts)  
        return shifts[next_idx]
    
    def update_date(date, next_shift, shifts_data):
        """
        Updates a datetime.

        Parameters
        ----------
        date : datetime
            Date being updated.
        next_shift : int
            Next shift index availble.
        shifts_data : dict
            Comprises information about the work shifts.

        Returns
        -------
        datetime
            Updated datetime.

        """
        start_time = shifts_data[next_shift]['start']
        return date.replace(hour=start_time.hour, minute=start_time.minute, second=0, microsecond=0)

    def get_free_analysts_tsp(analysts_info, analysts, ticket_tsp, aux_data, show):
        """
        Gets the analysts available at a particular timestamp.

        Parameters
        ----------
        analysts_info : dict
            Comprises all data about teams and their operators.
        analysts : list
            All operators working at a particular shift.
        ticket_tsp : int
            Ticket timestamp being analyzed.
        aux_data : UtilsParams
            Comprises auxiliar data, including outlier, priority levels, and other features.
        show : bool
            Show or not debugging.

        Returns
        -------
        free_analysts : list
            Operators available for treatment.

        """
        free_analysts = []
        for analyst in analysts:
            if analysts_info[analyst]["fixed_tsp"] <= ticket_tsp: 
                free_analysts.append(analyst)
            else:
                if show:
                    Utils.debug_and_log_data(aux_data.debug, aux_data.logger, f'{analyst} occupied until {analysts_info[analyst]["fixed"]}')
                
        if not free_analysts:
            Utils.debug_and_log_data(aux_data.debug, aux_data.logger, "No analysts available at the moment!")
        else:
            Utils.debug_and_log_data(aux_data.debug, aux_data.logger, f'Analysts available: {free_analysts}')

        return free_analysts
    
    def get_operators_in_shift(team_data, ticket_shift):
        """
        Gets operators working in a particular shift. 

        Parameters
        ----------
        team_data :  dict
            Comprises information about in a particular team.
        ticket_shift : int
            Ticket work shift being analyzed.

        Returns
        -------
        analysts : list
            List with operators working at a ticket shift.

        """
        analysts = []
        for analyst in team_data["analysts"]:
            if team_data["analysts"][analyst]["shift"] == ticket_shift:
                if team_data["analysts"][analyst]["active"]:
                    analysts.append(analyst)

        return analysts

    def get_next_shift_data(temp_date, curr_shift, shifts_data):
        """
        Gets information about the next shift.

        Parameters
        ----------
        temp_date : datetime
            Current datetime being analyzed.
        curr_shift : int
            Shift currently being analyzed.
        shifts_data : dict
            Comprises information about the work shifts.

        Returns
        -------
        temp_date : datetime
            Updated date.
        next_shift : int
            Updated work shift.

        """
        next_shift = Utils.get_next_shift(curr_shift, shifts_data)
        if next_shift == 0:
            print("Shift is on next day!")
            temp_date = Utils.update_date(temp_date, next_shift, shifts_data)
            temp_date = temp_date + timedelta(1)
        else:
            temp_date = Utils.update_date(temp_date, next_shift, shifts_data)

        return temp_date, next_shift
    
    def build_subfamily_action_teams(teams_data, family, subfamily, family_actions, family_steps_pool, subfamily_pool, aux_data):
        """
        Builds actions for each team on a particular subfamily.

        Parameters
        ----------
        teams_data : dict
            Comprises information about all treatment teams.
        family : str
            Family being analyzed.
        subfamily : str
            Subfamily being analyzed.
        family_actions : dict
            Comprises information about the actions taken in each family.
        family_steps_pool : dict
            Comprises data about the techniques and subfamilies for each family treatment.
        subfamily_pool : dict
            Comprises data about the subfamilies.
        aux_data : UtilsParams
            Comprises auxiliar data, including outlier, priority levels, and other features.

        Returns
        -------
        None.

        """    
        for curr_team in teams_data.keys():
            sub_action = Utils.build_subfamily_action(curr_team, family, subfamily, family_actions[family]["action"], family_steps_pool, aux_data)
            subfamily_pool[subfamily]['teams_actions'][curr_team] = sub_action 
            Utils.debug_and_log_data(aux_data.debug, aux_data.logger, f'Curr team: {curr_team} - Sub action: {sub_action}')

    def filter_string(string, substr):
        """
        Filters string(s) using substring(s).

        Parameters
        ----------
        string : list
            List of strings to analyze.
        substr : list
            List of substrings.

        Returns
        -------
        list
            List of string(s) containing the substring(s).

        """
        return [str for str in string if any(sub in str for sub in substr)]
        
    def flat_lists(_list):
        """
        Flats a list.

        Parameters
        ----------
        _list : list
            List of lists.

        Returns
        -------
        flat_list : list
            Single list.

        """
        flat_list = [item for sublist in _list for item in sublist]
        return flat_list
    
    def update_step_speed(steps_data, step, analyst_growth, improvement_type):
        """
        Updates the speed of a step

        Parameters
        ----------
        steps_data : dict
            Comprises information about the steps taken by an operator.
        step : str
            Step being analyzed.
        analyst_growth : float
            Operator growth factor.
        improvement_type : str
            Either "improve" or "worsen".

        Returns
        -------
        learning_rate : float
            Updated learning rate.
        speed_updated : float
            Updated speed.

        """
        learning_rate = steps_data[step]["learning_rate"]
        if improvement_type == "improve":
            learning_rate += 0.001
        else:
            learning_rate -= 0.001
        learning_rate = round(learning_rate, 3)
        speed_updated = Utils.get_speed(analyst_growth, learning_rate)
        return learning_rate, speed_updated  
    
    def update_family_resolution(ticket, families_resolution):
        """
        Updates family's resolution times and other statistics.

        Parameters
        ----------
        ticket : dict
            Ticket being analyzed.
        families_resolution : dict
            Comprises the mean duration spent to treat each family.

        Returns
        -------
        None.

        """
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
    
    def check_pending_tickets_priorities(analysts_info, analysts_in_shift, curr_team, ticket_tsp, tickets_info, priority_queues, aux_data):
        """
        Frees an operator when ticket is fixed.

        Parameters
        ----------
        analysts_info : dict
            Comprises all data about teams and their operators.
        analysts_in_shift : list
            Operators working in the current shift.
        curr_team : str
            Current team being analyzed.
        ticket_tsp : int
            Current ticket timestamp.
        tickets_info : dict
            Comprises information about all tickets.
        priority_queues : dict
            Comprises all the pending tickets, organized according to their priority.
        aux_data : UtilsParams
            Comprises auxiliar data, including outlier, priority levels, and other features.

        Returns
        -------
        None.

        """
        if Utils.check_tickets_in_team_queue(priority_queues, curr_team):
            min_time, min_tsp = Utils.find_min_analyst_endtime(analysts_info[curr_team]["analysts"], analysts_in_shift, aux_data)
            Utils.debug_and_log_data(aux_data.debug, aux_data.logger, f'Min endtime: {min_time}') 
            Utils.update_tickets_wait_time(curr_team, min_tsp, tickets_info, priority_queues, aux_data)
            Utils.update_tickets_priorities(curr_team, tickets_info, priority_queues, min_time, min_tsp, aux_data)

    def update_tickets_wait_time(team, min_curr_tsp, tickets_info, priority_queues, aux_data):
        """
        Updates the wait time of the pending tickets.

        Parameters
        ----------
        team : str
            Team being analyzed.
        min_curr_tsp : int
            Minimum timestamp analyzed.
        tickets_info : dict
            Comprises information about all tickets.
        priority_queues : dict
            Comprises all the pending tickets, organized according to their priority.
        aux_data : UtilsParams
            Comprises auxiliar data, including outlier, priority levels, and other features.

        Returns
        -------
        None.

        """  
        for priority in priority_queues[team]:
            if priority != aux_data.priority_levels: # No need to update the tickets with max priority since there are no greater levels
                Utils.debug_and_log_data(aux_data.debug, aux_data.logger, f'Priority studied {priority}')
                if priority_queues[team][priority]["tickets"]:
                    Utils.debug_and_log_data(aux_data.debug, aux_data.logger, f'Update pending tickets wait time in team {team} with priority {priority}')
                    for ticket_id in priority_queues[team][priority]["tickets"]:
                        time_in_queue = Utils.calculate_timestamp_diff(tickets_info[ticket_id]['added_queue_tsp'], min_curr_tsp, "minutes")    
                        tickets_info[ticket_id]['in_queue'] = time_in_queue
                        Utils.debug_and_log_data(aux_data.debug, aux_data.logger, f'Ticket {ticket_id} wait time in queue {priority}: {time_in_queue}')
              
    def update_tickets_priorities(team, tickets_info, priority_queues, min_time, min_time_tsp, aux_data):
        """
        Updates the priorities of the tickets.

        Parameters
        ----------
        team : str
            Team being analyzed.
        tickets_info : dict
            Comprises information about all tickets.
        priority_queues : dict
            Comprises all the pending tickets, organized according to their priority.
        min_time : datetime
            Minimum datetime analyzed.
        min_time_tsp : int
            Minimum timestamp analyzed.
        aux_data : UtilsParams
            Comprises auxiliar data, including outlier, priority levels, and other features.

        Returns
        -------
        None.

        """
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
                    avg = Utils.get_last_n_tickets_in_priority_queue(priority_queues[team][priority]["tickets"], tickets_info, 5, 2, aux_data)
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

        priority_queues[team] = new_priority_team
        
        if priorities_changed:
            Utils.debug_and_log_data(aux_data.debug, aux_data.logger, f'Tickets were added to priorities {priorities_changed}')
            for priority in priorities_changed:
                sorted_id_list = Utils.sort_priority_tickets(priority_queues[team][priority]["tickets"], tickets_info, aux_data)
                if sorted_id_list != None:
                    priority_queues[team][priority]["tickets"] = sorted_id_list
                    Utils.debug_and_log_data(aux_data.debug, aux_data.logger, f'After {team} {priority}: {priority_queues[team][priority]["tickets"]}')
                            
    def update_allocated_times(tickets_info, priority_queues, team, min_curr_time, min_curr_tsp, aux_data):
        """
        Updates allocation times of the pending tickets.

        Parameters
        ----------
        tickets_info : dict
            Comprises information about all tickets.
        priority_queues : dict
            Comprises all the pending tickets, organized according to their priority.
        team : str
            Team being analyzed.
        min_time : datetime
            Minimum datetime analyzed.
        min_time_tsp : int
            Minimum timestamp analyzed.
        aux_data : UtilsParams
            Comprises auxiliar data, including outlier, priority levels, and other features.

        Returns
        -------
        None.

        """
        Utils.debug_and_log_data(aux_data.debug, aux_data.logger, f'Curr priorities {priority_queues[team]}')
        for priority in priority_queues[team]:
            if priority_queues[team][priority]["tickets"]:
                for ticket_id in priority_queues[team][priority]["tickets"]:
                    if min_curr_tsp > tickets_info[ticket_id]['allocated_tsp']:
                        Utils.update_data(tickets_info[ticket_id], allocated = min_curr_time, allocated_tsp = min_curr_tsp, temp_allocated = min_curr_time, temp_allocated_tsp = min_curr_tsp)
                        Utils.debug_and_log_data(aux_data.debug, aux_data.logger, f'ticket {ticket_id} allocated updated: {tickets_info[ticket_id]["allocated"]}')
                        if "analyzed_in_shift" in tickets_info[ticket_id]:
                            del tickets_info[ticket_id]['analyzed_in_shift']
      
    def sort_priority_tickets(tickets, tickets_info, aux_data):
        """
        Sorts the pending tickets of a particular priority.

        Parameters
        ----------
        tickets : dict
            Comprises information about all tickets (with priorities updated).
        tickets_info : dict
            Comprises information about all tickets.
        aux_data : UtilsParams
            Comprises auxiliar data, including outlier, priority levels, and other features.

        Returns
        -------
        sorted_id_list : list
            List with tickets ids sorted.

        """  
        sorted_id_list = None
        if tickets and not Utils.is_sorted_by_datetime(tickets, tickets_info, aux_data.logger):
            sorted_id_list = sorted(tickets, key=lambda item: tickets_info[item]["raised_tsp"])
            Utils.debug_and_log_data(aux_data.debug, aux_data.logger, f'Sorted tickets ids: {sorted_id_list}') 
            
        return sorted_id_list
    
    def remove_ticket_priority_queue(ticket, priority_queues):
        """
        Removes a tickets from priority queue after being closed by analyst.

        Parameters
        ----------
        ticket : dict
            Ticket being analyzed.
        priority_queues : dict
            Comprises all the pending tickets, organized according to their priority.

        Returns
        -------
        None.

        """    
        ticket_id = ticket["id"]
        if ticket_id in priority_queues[ticket["team"]][ticket["priority"]]["tickets"]:
            priority_queues[ticket["team"]][ticket["priority"]]["tickets"].remove(ticket_id)
    
    def send_ticket_priority_queue(ticket, priority_queues, aux_data, issue):
        """
        Adds the ticket to its corresponding priority queue.

        Parameters
        ----------
        ticket : dict
            Ticket being analyzed.
        priority_queues : dict
            Comprises all the pending tickets, organized according to their priority.
        aux_data : UtilsParams
            Comprises auxiliar data, including outlier, priority levels, and other features.
        issue : int
            Type of issue that caused a ticket to be added to a priority queue (0 - shift is ending; 1 - All analysts are occupied; 2 - No operator is working at the current shift).

        Returns
        -------
        None.

        """    
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
            
    def get_last_n_tickets_in_priority_queue(priority_queue, tickets_info, n_tickets, multiplier, aux_data):
        """
        Calculates the average wait time of each priority queue based on the last n tickets (the multiplier helps assign a limit wait time per priority level).

        Parameters
        ----------
        priority_queue : dict
            Comprises all the pending tickets, organized according to their priority.
        tickets_info : dict
            Comprises information about all tickets.
        n_tickets : int
            Last n tickets.
        multiplier : int
            Multiplier to limit wait time per priority level.
        aux_data : UtilsParams
            Comprises auxiliar data, including outlier, priority levels, and other features.

        Returns
        -------
        avg : float
            Average wait time.

        """
        avg = None
        if len(priority_queue) > n_tickets:
            n_ticket_ids = priority_queue[-n_tickets:]
            Utils.debug_and_log_data(aux_data.debug, aux_data.logger, f'priority_queue: {priority_queue}. Last {n_tickets} tickets are: {n_ticket_ids}')
            n_total_in_queue = 0
            for ticket_id in n_ticket_ids:
                Utils.debug_and_log_data(aux_data.debug, aux_data.logger, f'Ticket id {ticket_id} in queue: {tickets_info[ticket_id]["in_queue"]} minutes')
                n_total_in_queue += tickets_info[ticket_id]['in_queue']
                
            avg = (n_total_in_queue / n_tickets) * multiplier
            
        return avg
    
    def find_min_analyst_endtime(analysts_data, analysts_in_shift, aux_data):
        """
        Gets the earliest ending datetime of all analysts.

        Parameters
        ----------
        analysts_data : dict
            Comprises all data the operators in a certain team
        analysts_in_shift : list
            Operators working in the current shift.
        aux_data : UtilsParams
            Comprises auxiliar data, including outlier, priority levels, and other features.

        Returns
        -------
        min_time : datetime
            Minimum datetime.
        min_curr_tsp : int
            Minimum timestamp.

        """    
        min_time = None
        min_curr_tsp = float('inf')
        for analyst in analysts_in_shift:
            Utils.debug_and_log_data(aux_data.debug, aux_data.logger, f'{analyst} - {analysts_data[analyst]["fixed"]}')
            if min_curr_tsp >= analysts_data[analyst]["fixed_tsp"]:
                min_time = analysts_data[analyst]["fixed"]
                min_curr_tsp = analysts_data[analyst]["fixed_tsp"]
                
        return min_time, min_curr_tsp
    
    def update_analysts_in_next_shift(analysts_data, team, start_date, prev_shift, curr_shift, gen_analysts_info, tt_analysts_info, shifts_data, aux_data):
        """
        Prepares the analysts of the next shift and cleans data from analysts of the shift closed.

        Parameters
        ----------
        analysts_data : dict
            Comprises all data the operators in a certain team
        team : str
            Team being analyzed.
        start_date : datetime
            Start datetime of the next shift.
        prev_shift : int
            Previous work shift.
        curr_shift : int
            Current work shift.
        gen_analysts_info : dict
            Comprises all data about teams and their operators (in the generator that serves as emulator).
        tt_analysts_info : dict
            Comprises all data about teams and their operators (in the recommender system).
        shifts_data : dict
            Comprises information about the work shifts.
        aux_data : UtilsParams
            Comprises auxiliar data, including outlier, priority levels, and other features.

        Returns
        -------
        None.

        """
        Utils.debug_and_log_data(aux_data.debug, aux_data.logger, f'Shift: {curr_shift}')
        if prev_shift != curr_shift:            
            Utils.debug_and_log_data(aux_data.debug, aux_data.logger, f'Shift changed from {prev_shift} to {curr_shift}')
            for analyst in analysts_data:
                if analysts_data[analyst]["shift"] == prev_shift:
                    if gen_analysts_info != None:
                        Utils.update_data(gen_analysts_info[team]["analysts"][analyst], assigned_ticket = None)
                    if tt_analysts_info != None:
                        Utils.update_data(tt_analysts_info[team]["analysts"][analyst], assigned_ticket = None)
                    
            Utils.debug_and_log_data(aux_data.debug, aux_data.logger, f'All operators from shift {prev_shift} are now free')
            start_date_utc, start_date_tsp = Utils.set_date_start_shift(start_date, shifts_data)
        
            for analyst in analysts_data:
                if analysts_data[analyst]["shift"] == curr_shift:
                    if gen_analysts_info != None:
                        Utils.update_data(gen_analysts_info[team]["analysts"][analyst], fixed = start_date_utc, fixed_tsp = start_date_tsp, assigned_ticket = None)
                    if tt_analysts_info != None:
                        Utils.update_data(tt_analysts_info[team]["analysts"][analyst], fixed = start_date_utc, fixed_tsp = start_date_tsp, assigned_ticket = None)
        
            Utils.debug_and_log_data(aux_data.debug, aux_data.logger, f'All operators from shift {curr_shift} are now available to treat tickets') 

    def set_date_start_shift(start_date, shifts_data):
        """
        Sets the starting date of the operators of the current shift.

        Parameters
        ----------
        start_date : datetime
            Start datetime of the next shift.
        shifts_data : dict
            Comprises information about the work shifts.

        Returns
        -------
        start_date_combined_utc : datetime
            Start datetime of the next shift (with updated time)
        int
            Start timestamp of the next shift (with updated time).

        """        
        start_date_date = start_date.date()
        start_date_shift = Utils.get_ticket_shift(start_date.time(), shifts_data)
        start_date_combined = datetime.combine(start_date_date, shifts_data[start_date_shift]["start"])
        start_date_combined_utc = pytz.UTC.localize(start_date_combined)
        
        return start_date_combined_utc, start_date_combined_utc.timestamp()
        
    def check_next_existing_teams(tickets, team):
        """
        Checks if the next teams have any tickets to solve.

        Parameters
        ----------
        tickets : dict
            Comprises information about all tickets.
        team : str
            Team being analyzed.

        Returns
        -------
        None.

        """
        next_teams = Utils.get_remaining_teams(team, list(tickets))      
        if next_teams:
            if not tickets[next_teams[0]]:
                for remove_team in next_teams:
                    if not tickets[remove_team]:
                        del tickets[remove_team]
            else:
                if not Utils.is_dict_sorted(tickets[next_teams[0]]):
                    print("Not sorted")
                    sorted_items = sorted(tickets[next_teams[0]].items(), key=lambda x: x[1]['raised_tsp'])
                    tickets[next_teams[0]] = {i: value for i, (key, value) in enumerate(sorted_items)}    
    
    def process_tickets_solved(tickets, teams, subfamily_pool, logger):
        """
        Creates a dataframe from all tickets treated by the different teams.

        Parameters
        ----------
        tickets : dict
            Comprises information about all tickets.
        teams : list
            All teams involved in ticket treatment.
        subfamily_pool : dict
            Comprises data about the subfamilies.
        generation : bool
            Whether this task is related to ticket treatment or not (can be applied to other types of operations).
        logger : Logger
            Logging module used for recording and debuging.

        Returns
        -------
        dict
            All tickets treated.

        """    
        if len(tickets) == 1:
            return tickets[list(tickets.keys())[0]]
        else:
            return Utils.merge_team_tickets(tickets, teams, subfamily_pool, logger)
    
    def check_teams_tickets(all_tickets):
        """
        Checks if all teams have treated the tickets.

        Parameters
        ----------
        all_tickets : dict
            Comprises information about all tickets.

        Returns
        -------
        bool
            DESCRIPTION.

        """    
        for team in all_tickets:
            if bool(all_tickets[team]):
                return True
                
        return False
    
    def get_next_ticket_different_teams(all_tickets):
        """
        Gets the next ticket treated from different teams.

        Parameters
        ----------
        all_tickets : dict
            Comprises information about all tickets.

        Returns
        -------
        key_picked : int
            Ticket id picked.
        ticket : dict
            Ticket picked.
        team_picked : str
            Team picked.

        """
        min_raised_tsp, ticket, team_picked, key_picked = None, None, None, None
        
        for team in all_tickets:
            if bool(all_tickets[team]):
                first_key = list(all_tickets[team].keys())[0]
                first_ticket = all_tickets[team][first_key]
                if min_raised_tsp == None:
                    key_picked = first_key
                    ticket = first_ticket
                    min_raised_tsp = first_ticket["raised_tsp"]
                    team_picked = team
                else:
                    if min_raised_tsp > first_ticket["raised_tsp"]:
                        key_picked = first_key
                        ticket = first_ticket
                        min_raised_tsp = first_ticket["raised_tsp"]
                        team_picked = team
               
        return key_picked, ticket, team_picked
    
    def get_increment_with_id_greater(curr_id, replicated_ids):
        """
        Updates ticket id to include replicated tickets.

        Parameters
        ----------
        curr_id : int
            Current ticket id analyzed.
        replicated_ids : list
            List with replicated ids.

        Returns
        -------
        increment : TYPE
            DESCRIPTION.

        """    
        increment = 0
        for element in replicated_ids:
            if element < curr_id:
                increment += 1
        return increment
    
    def merge_team_tickets(all_tickets, all_teams, subfamily_pool, logger):
        """
        Creates a dictionary by merging all tickets from different teams

        Parameters
        ----------
        all_tickets : dict
            Comprises information about all tickets.
        all_teams : list
            All teams involved in ticket treatment.
        subfamily_pool : dict
            Comprises data about the subfamilies.
        generation : bool
            Whether this task is related to ticket treatment or not (can be applied to other types of operations).
        logger : Logger
            Logging module used for recording and debuging.

        Returns
        -------
        new_dict : dict
            All tickets treated by different teams.

        """    
        new_dict, replicated_tickets, tickets_inheritance = {}, {}, {}
        curr_id, n_replicated = 0, 0
        
        while Utils.check_teams_tickets(all_tickets):
            key, next_ticket, team = Utils.get_next_ticket_different_teams(all_tickets)
            new_dict[curr_id] = next_ticket
            new_dict[curr_id]["id"] = curr_id
            
            if team == all_teams[0]:
                next_team = Utils.get_next_team(team, list(all_teams))
                if next_team not in replicated_tickets:
                    replicated_tickets[next_team] = []
                    
                Utils.check_similar_coordinated_tickets(new_dict[curr_id], new_dict, tickets_inheritance, subfamily_pool, logger)
                     
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
                            if "analyzed" not in new_dict[prev_ticket]:
                                new_dict[prev_ticket]["analyzed"] = True
                                new_replicated_id = replicated_tickets[prev_team][-1]
                                new_dict[curr_id]["replicated"] = new_replicated_id
                                break
                    
                replicated_tickets[team].append(curr_id)
                n_replicated += 1

            del all_tickets[team][key]
            curr_id += 1
            
        return new_dict
    
    def get_next_teams(team, all_teams):
        """
        Gets the upper teams compared to a current one.

        Parameters
        ----------
        team : str
            Current team analyzed.
        all_teams : list
            All teams involved in ticket treatment.

        Returns
        -------
        next_teams : list
            Next upper teams.

        """
        next_teams = []
        if team in all_teams:
            curr_team_idx = all_teams.index(team)
            for next_team_idx in range(curr_team_idx, len(all_teams)):
                next_teams.append(all_teams[next_team_idx])
    
        return next_teams

    def get_function_time_spent(curr_time):
        """
        Gets the time spent by a function.

        Parameters
        ----------
        curr_time : int
            Timestamp analyzed.

        Returns
        -------
        wait_time : int
            Time spent (in seconds).
        curr_time : int
            Current timestamp.

        """        
        end = datetime.now()
        time_delta = end - curr_time
        wait_time = time_delta.total_seconds()
        curr_time = end

        return wait_time, curr_time
    
    def create_log(path, name, active):
        """
        Creates log files for debugging purposes.

        Parameters
        ----------
        path : str
            Output path.
        name : str
            logger name.
        active : bool
            If the logger is active or not.

        Returns
        -------
        logger : Logger
            Logging module used for recording and debuging.

        """    
        log_file = f'{path}/{name}.txt'
        logger = logging.getLogger(name)
        
        if logger.hasHandlers():
            print("Logger with the same name exists!")
            logger.handlers = []
            logger.setLevel(logging.NOTSET)
            
        if active:
            print("Logger Active")
            file_handler = logging.FileHandler(log_file, mode = 'w')
            formatter = logging.Formatter('%(message)s')
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)  
            logger.setLevel(logging.INFO)
        else:
            print("Logger Disabled")
        
        logger.propagate = False
        return logger

    def log_data(logger, message):
        """
        Logs data with a message.

        Parameters
        ----------
        logger : Logger
            Logging module used for recording and debuging.
        message : str
            Message content.

        Returns
        -------
        None.

        """
        if len(logger.handlers) > 0:
            logger.info(message)
      
    def debug_and_log_data(debug, logger, message):
        """
        Logs and debugs the code.

        Parameters
        ----------
        debug : bool
            If debugging is active or not.
        logger : Logger
            Logging module used for recording and debuging.
        message : str
            Debug and log message.

        Returns
        -------
        None.

        """  
        if debug:
            print(message)
            
        if logger.hasHandlers():
            logger.info(message)
                
    def save_generator_data(output_path, family_info, family_steps, subfamily_info, analysts_steps_info, special_steps):
        """
        Stores the generator data into a JSON file.

        Parameters
        ----------
        output_path : str
            Output path to save the JSON file.
        family_info : dict
            Comprises information about the families.
        family_steps : dict
            Comprises information about the steps used to treat the families.
        subfamily_info : dict
            Comprises information about the subfamilies.
        analysts_steps_info : dict
            Comprises information about the steps used by operators to treat the tickets.
        special_steps : dict
            Comprises information about special steps.

        Returns
        -------
        None.

        """
        with open(output_path, 'w') as fd:
            fd.write(json.dumps([family_info, family_steps, subfamily_info, analysts_steps_info, special_steps], indent=2, default=str)) 
        print("Generator's info saved")
        
    def save_input_data(output_path, generation_params, other_params):
        """
        Stores the user input into a JSON file.

        Parameters
        ----------
        output_path : str
            Output path to save the JSON file.
        generation_params : dict
            Comprises all data about parameters related to ticket and team generation.
        other_params : dict
            Comprises all data about parameters necessary besides generation and treatment.

        Returns
        -------
        None.

        """
        with open(output_path, 'w') as fd:
            fd.write(json.dumps([generation_params, other_params], indent=2, default=str)) 
        print("Input's info saved")
        
    def set_seed(seed):
        """
        Sets the seed for random tasks.

        Parameters
        ----------
        seed : int
            Seed value.

        Returns
        -------
        None.

        """
        if seed != None:
            np.random.seed(seed)
            random.seed(seed)
    
    def get_max_min_in_dict(data, is_min, feature):
        """
        Gets the maximum/minimum value and key of a dictionary based on a particular feature.

        Parameters
        ----------
        data : dict
            Dictionary being analyzed.
        is_min : bool
            It it searches for the minimum or not (maximum).
        feature : str
            Feature to be searcher.

        Returns
        -------
        best_data_key : str
            Key with min/max value.
        value : str
            Value corresponding to the best_data_key.

        """    
        best_data_key, value = 0,0
        if not is_min:
            best_data_key = max(data, key=lambda data_key: data[data_key][feature])
            value = data[best_data_key][feature]
        else:
            best_data_key = min(data, key=lambda data_key: data[data_key][feature])
            value = data[best_data_key][feature]

        return best_data_key, value
    
    def calculate_average_time(data, time_type):
        """
        Calculates average wait time.

        Parameters
        ----------
        data : dict
            Comprises information the shift data.
        time_type : str
            Could be "time_spent" or "wait_time".

        Returns
        -------
        float
            Time spent or wait time.

        """
        if time_type == "time_spent":
            return data['time_spent'] / data['n_tickets']
        else:
            return data['wait_time'] / data['n_tickets']
        
    def get_incidents_treated_in_shift(family, subfamily, time_spent, incidents_performance):
        """
        Gets the incidents treated in a particular shift.

        Parameters
        ----------
        family : str
            Family being analyzed.
        subfamily : str
            Subfamily being analyzed.
        time_spent : float
            Time spent in treating the subfamily.
        incidents_performance : dict
            Comprises information about the ticket treatment performance.

        Returns
        -------
        incidents_performance : TYPE
            DESCRIPTION.

        """
        if family not in incidents_performance:
            incidents_performance[family] = {}
                
        if subfamily not in incidents_performance[family]:
            incidents_performance[family][subfamily] = {}
            incidents_performance[family][subfamily]["n_tickets"] = 0
            incidents_performance[family][subfamily]["time_spent"] = 0
        incidents_performance[family][subfamily]["n_tickets"] += 1
        incidents_performance[family][subfamily]["time_spent"] += time_spent
        
        return incidents_performance
    
    def analyse_shifts_performance(shifts_data, teams_summary, team_analysts):
        """
        Assesses the performance of the teams and their analysts in the different shifts.

        Parameters
        ----------
        shifts_data : dict
            Comprises information about the work shifts.
        teams_summary : dict
            Comprises statistics about the treatment performed by different teams.
        team_analysts : list
            List of operators in the teams.

        Returns
        -------
        None.

        """    
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

    def copy_dict(copied_dict, original_dict):
        """
        Builds a copy of a dictionary-

        Parameters
        ----------
        copied_dict : dict
            Copied dictionary.
        original_dict : dict
            Dictionary to be copied.

        Returns
        -------
        None.

        """        
        for key, value in original_dict.items():
            if isinstance(value, (list, set)):
                copied_dict.update({key: set(value) if isinstance(value, set) else list(value)})
            elif isinstance(value, dict):
                copied_dict[key] = {}
                Utils.copy_dict(copied_dict[key], value)
            else:
                copied_dict.update({key: value})
                
    def contains_files(directory):
        """
        Checks if a dictory contains files

        Parameters
        ----------
        directory : str
            Directory path.

        Returns
        -------
        bool
            If there are or not any files in the directory and its subdirectories.

        """
        has_files = any(files for _, _, files in os.walk(directory))
        if has_files:
            print("There are files in the directory or its subdirectories")
            return True
        else:
            print("No files found, only folders")
            return False