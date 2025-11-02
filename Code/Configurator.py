"""
Created on Fri Apr  2 12:10:27 2021

@author: Leonardo Ferreira
@goal: Reads the configuration file and manages several parameters for the generation
"""

from Code.Utils import Utils

from PyQt5.QtWidgets import QFileDialog
import os, json, string, random, ijson, sys, pytz
import pandas as pd
from datetime import datetime
import pendulum
import numpy as np
import matplotlib.pyplot as plt
from sklearn.experimental import enable_iterative_imputer
from sklearn.impute import IterativeImputer
from ruamel.yaml import YAML

class Configurator:
    def read_configuration_file(domain, path):
        """
        Reads the configuration file

        Parameters
        ----------
        domain : str
            Generation Domain.
        path : str
            Path where the configuration file is located.

        Returns
        -------
        config_data : dict
            Comprises the data used for the generation and treatment of the datasets (retrieved from an external file).

        """
        
        config_data = {}
        try:
            yaml = YAML(typ='rt')
            with open(path, "r") as fh:
                config_data = yaml.load(fh)
                return config_data
        except FileNotFoundError:
            print("Couldn't find configuration file!" )
            
    def check_param_in_config(config, param):
        """
        Checks if param exists in configuration file.

        Parameters
        ----------
        config : dict
            Comprises the data used for the generation and treatment of the datasets.
        param : str
            Concrete attribute to be searched within config.

        Returns
        -------
        bool
            Existing or non-existent attribute.

        """

        if param in config.keys():
            return True
        else:
            print(f'The config does not have the param {param}')
    
    def load_configurations(domain):
        """
        Loads several parameters from the configuration file.    

        Parameters
        ----------
        domain : str
            Generation Domain.

        Raises
        ------
        ValueError
            if the configuration cannot be read and parsed.

        Returns
        -------
        interface_params : dict
            Comprises all configurations related to the interface.
        generation_params : dict
            Comprises all configurations related to the dataset generation (include multiple tickets).
        treatment_params : dict
            Comprises all configurations related to the ticket treatment.
        suspicious_countries : dict
            Comprises data related to countries characterized by potential suspicious activity.

        """
        path =  f'Configurations/{domain}/Init_cfg.yaml'
        config_data = Configurator.read_configuration_file(domain, path)

        interface_params, generation_params, treatment_params = {}, {}, {}
        generation_params["suspicious_countries"] = {}
        
        interface_params["outlier_selector"], interface_params["suspicious_selector"], interface_params["multiple_attack_selector"] = True, True, False
        generation_params["ip_selected_idx"], generation_params["format_selected_idx"] = 0, 0
        generation_params["family_selection"] = "Random"
        generation_params["ip_selector"], generation_params["ticket_seasonality_selector"], generation_params["family_seasonality_selector"], generation_params["techniques_seasonality_selector"], generation_params["ticket_escalation_selector"] = True, True, True, False, True
        treatment_params["ticket_similarity_selector"], treatment_params["ticket_verification_selector"] = True, True
        generation_params["ticket_growth_selector"] = True
        try:
            interface_params["generation_mode"] = config_data["generation_parameters"]["generation_mode"]
            generation_params['n_tickets'] = config_data["generation_parameters"]['n_tickets']
            generation_params['ticket_growth_rate'] = config_data["generation_parameters"]['ticket_growth_rate']
            generation_params['families_number'] = config_data["generation_parameters"]['families_number']
            generation_params['minsubfamilies_number'] = config_data["generation_parameters"]['minsubfamilies_number']
            generation_params['maxsubfamilies_number'] = config_data["generation_parameters"]['maxsubfamilies_number']
            generation_params['techniques_number'] = config_data["generation_parameters"]['techniques_number']
            generation_params['minsubtechniques_number'] = config_data["generation_parameters"]['minsubtechniques_number']
            generation_params['maxsubtechniques_number'] = config_data["generation_parameters"]['maxsubtechniques_number']
            generation_params['max_transfer_steps'] = config_data["generation_parameters"]['max_transfer_steps']
            generation_params['seed'] = config_data["generation_parameters"]['seed']
            generation_params["start_date"] = config_data["generation_parameters"]["start_date"]
            generation_params["end_date"] = config_data["generation_parameters"]["end_date"]
            generation_params["outlier_rate"] = config_data["generation_parameters"]['outlier_rate']
            generation_params["outlier_cost"] = config_data["generation_parameters"]['outlier_cost']
            generation_params["escalate_rate_percentage"] = config_data["generation_parameters"]['escalate_rate_percentage']
            generation_params["min_coordinated_attack"] = config_data["generation_parameters"]['min_coordinated_attack']
            generation_params["max_coordinated_attack"] = config_data["generation_parameters"]['max_coordinated_attack']
            generation_params["min_coordinated_attack_minutes"] = config_data["generation_parameters"]['min_coordinated_attack_minutes']
            generation_params["max_coordinated_attack_minutes"] = config_data["generation_parameters"]['max_coordinated_attack_minutes']
            generation_params["min_subtechnique_rate"] = config_data["generation_parameters"]['min_subtechnique_rate']
            generation_params["max_subtechnique_rate"] = config_data["generation_parameters"]['max_subtechnique_rate']
            generation_params["min_subtechnique_cost"] = config_data["generation_parameters"]['min_subtechnique_cost']
            generation_params["max_subtechnique_cost"] = config_data["generation_parameters"]['max_subtechnique_cost']
            generation_params["suspicious_subfamily"] = config_data["generation_parameters"]['suspicious_subfamily']
            generation_params["clients_number"] = config_data["generation_parameters"]['clients_number']
            generation_params["distribution_mode"] = config_data["generation_parameters"]["distribution_mode"]
            generation_params["reset_analysts_data"] = config_data["generation_parameters"]["reset_analysts_data"]
            generation_params["balanced_shifts"] = config_data["generation_parameters"]["balanced_shifts"]
            generation_params["debug"] = config_data["generation_parameters"]["debug"]
            generation_params["logger_active"] = config_data["generation_parameters"]["logger_active"]
            generation_params["print_plots"] = config_data["generation_parameters"]["print_plots"]
            generation_params["use_default_family"] = config_data["generation_parameters"]["use_default_family"]
            generation_params["time_equal_probabilities"] = config_data["generation_parameters"]["time_equal_probabilities"]
            generation_params["week_equal_probabilities"] = config_data["generation_parameters"]["week_equal_probabilities"]
            generation_params["max_priority_levels"] = config_data["generation_parameters"]["max_priority_levels"]
            generation_params["with_ip"] = config_data["generation_parameters"]['with_ip']
            generation_params["action_operations"] = config_data["action_operations"]
            generation_params["ips_pool"] = config_data["ips_pool"]
            generation_params["default_alert_pool"] = config_data["families"]
            generation_params["family_time_4h"] = config_data["family_time_4h"]
            generation_params["week_time"] = config_data["week_time"]
            generation_params["day_ticket_spikes"] = config_data["day_ticket_spikes"]
            generation_params["analysts_skills"] = config_data["analysts_info"]
            
            treatment_params["day_stages"] = config_data["day_stages"]
            generation_params["shifts"] = config_data["generation_parameters"]["shifts"]
            treatment_params["analyst_subfamily_action_probability"] = config_data["generation_parameters"]['analyst_subfamily_action_probability']
            treatment_params["analyst_same_action_probability"] = config_data["generation_parameters"]['analyst_same_action_probability']
            treatment_params["actions_similarity"] = config_data["generation_parameters"]['actions_similarity']
            treatment_params["min_learning_counter"] = config_data["generation_parameters"]['min_learning_counter']
            treatment_params["max_learning_counter"] = config_data["generation_parameters"]['max_learning_counter']

            suspicious_countries = config_data["suspicious_countries"]
            suspicious_countries = dict(sorted(suspicious_countries.items()))
        except KeyError as e:
            if str(e).find("generation"):
                interface_params["suspicious_selector"] = False	
            raise ValueError(f'Could not load {domain} configuration file. Error {e}')

        if generation_params['ticket_growth_rate'] == 0:
            generation_params["ticket_growth_selector"] = False

        print("Cybersecurity configuration file successfully loaded!") 
        return interface_params, generation_params, treatment_params, suspicious_countries

    def update_configuration_data(param, content, domain, path):
        """
        Updates the configuration file.

        Parameters
        ----------
        param : str
             Attribute to be updated.
        content : dict
            Updated content.
        domain : str
            Domain of the configuration file.
        path : str
            Path of the configuration file to be updated.

        Returns
        -------
        None.

        """
        config_data = Configurator.read_configuration_file(domain, path)
        config_data[param].update(content)
        
        yaml = YAML(typ='rt')
        with open(path, 'w') as f:
            yaml.dump(config_data, f)
        print(f'{domain} custom configuration saved!')


    def read_configuration_section(domain, section):
        """
        Reads a particular part of the configuration file.        

        Parameters
        ----------
        domain : str
            Domain of the configuration file.
        section : str
            Section to be read.

        Returns
        -------
        TYPE
            Content of the section requested.

        """
        path = f'Configurations/{domain}/Init_cfg.yaml'
        config_data = Configurator.read_configuration_file(domain, path)
        
        return config_data[section] 
                 
    def load_configuration_data(window, path):
        """
        Shows a QFileDialog window and picks the configuration file.

        Parameters
        ----------
        window : TeamAnalystWindow
            Window where the data is requested.
        path : str
            Path of the configuration file.

        Returns
        -------
        filename : dict
            Comprises all the information present in the configuration file.

        """
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        filename, _ = QFileDialog.getOpenFileName(window, "Open File", path, "", options=options)
        return filename
    
    def save_dialog(window):
        """
        Shows a QFileDialog window and stores the configuration file.

        Parameters
        ----------
        window : TeamAnalystWindow
            Window where the data is updated.

        Returns
        -------
        filename : dict
            Comprises all the information present in the configuration file.

        """
        options = QFileDialog.Options()
        filename, _ = QFileDialog.getSaveFileName(window, 'Save as... File', 'Custom_cfg', filter="YAML (*.yaml)",options=options)
        return filename
    
    def save_new_config_file(domain, param, content, new_file):
        """
        Stores a new configuration file defined by the user

        Parameters
        ----------
        domain : str
            Generation domain.
        param : str
            Attribute being created.
        content : dict
            Content of the attribute added.
        new_file : str
            Name of the new configuration file.

        Returns
        -------
        None.

        """
        path =  f'Configurations/{domain}/Init_cfg.yaml'
        config_data = Configurator.read_configuration_file(domain, path)
        
        config_data[param].update(content)
        with open(new_file, 'w') as f:
            ruamel.yaml.dump(config_data, f, Dumper=ruamel.yaml.RoundTripDumper)
            
        print("New configuration file saved!")
    
    def get_countries_data(path, countries_picked):
        """
        Gets the countries and their IPs.

        Parameters
        ----------
        path : str
            Countries file path.
        countries_picked : list
            List of countries to be used in the generation.

        Returns
        -------
        countries : dict
            Comprises the countries and information regarding their timezones and IPs.

        """    
        countries = {}
        with open(path, "rb") as f:
            for countries_data in ijson.items(f, "countries"):
                print("Number of countries", len(countries_data.keys()))
                for p in countries_picked:
                    countries[p] = {}
                    countries[p]["timezones"] = countries_data[p]["timezones"]
                    if len(countries_data[p]["ips"]) > 5:
                        countries[p]["ips"] = random.sample(countries_data[p]["ips"], 5)
                    else:
                        countries[p]["ips"] = countries_data[p]["ips"]
                        
        return countries
    
    def get_countries_names(path):
        """
        Gets the name of the countries.

        Parameters
        ----------
        path : str
            Countries file path.

        Returns
        -------
        countries : list
            List of the countries names.

        """
        countries = []
        with open(path, "rb") as f:
            for countries_data in ijson.items(f, "countries"):
                countries = list(countries_data.keys())
        #print("Countries:", countries)
        return countries

    def solve_family_anomalies(dataset):
        """
        Handles null families and subfamilies in the real dataset.

        Parameters
        ----------
        dataset : dataframe
            Dataframe of the real dataset.

        Returns
        -------
        test_dict : dict
            Dataset in dict format.
        dataset : dataframe
            Updated dataset.

        """
        families_info = {}
        incidents_info = dataset.groupby(['Family', 'Subfamily']).size()
        test_dict = dataset.to_dict("index")

        for incident_data, count in incidents_info.items():
            if count != 0:
                family = incident_data[0]
                subfamily = incident_data[1]
                if family not in families_info:
                    families_info[family] = []
                if incident_data not in families_info[family]:
                    families_info[family].append(subfamily)

        for i in test_dict:
            if pd.isnull(test_dict[i]['Family']):
                if pd.isnull(test_dict[i]['Subfamily']):
                    family_picked = random.choice(list(families_info.keys()))
                    dataset.loc[dataset["ID"] == test_dict[i]['ID'], "Family"] = family_picked
                    test_dict[i]['Family'] = family_picked
                    subfamily_picked = random.choice(families_info[family_picked])
                    dataset.loc[dataset["ID"] == test_dict[i]['ID'], "Subfamily"] = subfamily_picked
                    test_dict[i]['Subfamily'] = subfamily_picked
                else:    
                    family_picked = test_dict[i]['Subfamily'].split("-")[0]
                    if family_picked not in dataset['Family'].cat.categories:
                        dataset['Family'] = dataset['Family'].cat.add_categories(family_picked)
                        families_info[family_picked] = []
                    if test_dict[i]['Subfamily'] not in families_info[family_picked]:
                        families_info[family_picked].append(test_dict[i]['Subfamily'])
                        
                    dataset.loc[dataset["ID"] == test_dict[i]['ID'], "Family"] = family_picked
                    test_dict[i]['Family'] = family_picked
                    
        return test_dict, dataset
    
    def convert_timestamps(list_):
        """
        Converts timestamps into pendulum instances (if possible).

        Parameters
        ----------
        list_ : list
            Timestamps of the steps used in ticket treatment.

        Returns
        -------
        temp: list
            Updated list of timestamps with correct format.

        """
        temp = []
        if len(list_) != 1:
            for k in list_:
                try:
                    #print(k)
                    dt_object = pendulum.from_timestamp(int(float(k)))
                    temp.append(dt_object.replace(tzinfo=None))
                except:
                    return []
        return temp
    
    def convert_timestamp_to_datetimelist(timestamps):
        """
        Checks for null and wrong timestamp format.     

        Parameters
        ----------
        timestamps : str
            Timestamps to be analyzed.

        Returns
        -------
        result : list
            Timestamps with the correct format.

        """
        
        if pd.isnull(timestamps):
            result = -1
        else:
            result = timestamps.replace('[', '')
            result = result.replace(']', '')
            result = result.split(', ')
            result = Configurator.convert_timestamps(result)
            if not result:
                print("Entry removed!")
                result = 0
        return result
    
    def solve_timestamp_anomalies(dataset, temp_dict, subfamilies_mean):
        """
        Fixes anomalies with the timestamps    

        Parameters
        ----------
        dataset : dataset
            Dataset being analyzed.
        temp_dict : dict
            Dataset in dict format for easier attribute access.
        subfamilies_mean : dict
            Comprises information about the time spent and number of occorrences of each subfamily.

        Returns
        -------
        dataset : dataframe
            Updated dataframe.

        """
        ticket_durations, raised = [], []

        for i in temp_dict:
            if temp_dict[i]['Steps'] == -1:
                print("Index:", i)
                subfamily = temp_dict[i]["Subfamily"]
                sub_mean = int(subfamilies_mean[subfamily]["time_spent"] / subfamilies_mean[subfamily]["count"])
                sub_mean = random.randint(sub_mean - 4 , sub_mean + 4)
                subfamilies_mean[subfamily]["time_spent"] += sub_mean
                subfamilies_mean[subfamily]["count"] += 1
                fixed_date = subfamilies_mean[subfamily]["min init date"].add(minutes = sub_mean)
                dataset.loc[dataset["ID"] == temp_dict[i]['ID'], "Fixed"] = fixed_date
                ticket_durations.append(sub_mean)
                raised.append(subfamilies_mean[subfamily]["min init date"])
                subfamilies_mean[subfamily]["min init date"] = fixed_date
            else:
                min_date = min(temp_dict[i]['Steps'])
                max_date = max(temp_dict[i]['Steps'])
                time_diff = max_date - min_date
                minutes = round(time_diff.total_seconds() / 60)
                ticket_durations.append(minutes)
                raised.append(min_date)
            
        dataset["Ticket Duration"] = ticket_durations
        dataset["raised"] = raised
        return dataset
    
    def get_ticket_duration(start, end, subfamily):
        """
        Gets the total duration of a ticket    

        Parameters
        ----------
        start : int
            First step timestamp.
        end : int
            Last step timestamp.
        subfamily : str
            Subfamily being analyzed.

        Returns
        -------
        minutes : int
            Ticket duration in minutes.

        """
        time_diff = end - start
        minutes = round(time_diff.total_seconds() / 60)
        return minutes
    
    def get_subfamilies_mean(dataset, temp_dict):
        """
        Gets the mean of each subfamily.    

        Parameters
        ----------
        dataset : dataframe
            Dataset being analyzed.
        temp_dict : dict
            Dataset in dict format for easier access.

        Returns
        -------
        subfamilies_mean : dict
            Comprises information about the time spent and number of occorrences of each subfamily.

        """
        subfamilies_mean = {}
        all_subfamilies = dataset['Subfamily'].unique()
        all_subfamilies = [item for item in all_subfamilies if not(pd.isnull(item)) == True]
        min_init_date = pendulum.datetime(2100, 6, 1).replace(tzinfo=None)
        
        for i in temp_dict:
            if temp_dict[i]["Steps"] != -1:
                subfamily = temp_dict[i]["Subfamily"]
                if subfamily not in subfamilies_mean:
                    subfamilies_mean[subfamily] = {}
                    subfamilies_mean[subfamily]["time_spent"] = 0
                    subfamilies_mean[subfamily]["count"] = 1
                    subfamilies_mean[subfamily]["min init date"] = min_init_date
                else:
                    subfamilies_mean[subfamily]["count"] += 1
                    
                min_date = min(temp_dict[i]["Steps"])
                max_date = max(temp_dict[i]["Steps"])
                time_spent = Configurator.get_ticket_duration(min_date, max_date, subfamily)
                subfamilies_mean[subfamily]["time_spent"] += time_spent
                    
                if min_date < subfamilies_mean[subfamily]["min init date"]:
                    subfamilies_mean[subfamily]["min init date"] = min_date
                
        avg = 0
        for subfamily in subfamilies_mean:
            avg += subfamilies_mean[subfamily]["time_spent"] /subfamilies_mean[subfamily]["count"]

        avg = avg/len(subfamilies_mean)
        for sub in all_subfamilies:
            if sub not in subfamilies_mean:
                subfamilies_mean[subfamily] = {}
                subfamilies_mean["time_spent"] = avg
                subfamilies_mean["count"] = 1
               
        return subfamilies_mean
        
    def get_ticket_seasonality(filename, is_database, connection, show_real_data):
        """
        Gets the seasonality of the real dataset (either from databases or custom samples).
        The seasonality of each family over the year is converted in probability weights.
        BEWARE! MUST be adapted to the real dataset explored (processed and cleaned).
        Other classes require changing of names used to link with real data processed.

        Parameters
        ----------
        filename : str
            Name of the file.
        is_database : bool
            If it is a database or not (csv or excel).
        connection : SQLConnectionWindow
            Connection is established in SQLConnectionWindow using psycopg2.
        show_real_data : bool
            Plot or not the real data.

        Returns
        -------
        ticket_seasonality: dict
            Comprises the daily seasonality of the real tickets.
        family_seasonality: dict
            Comprises the monthly seasonality of the real families.
        family_mean_duration: dict
            Comprises the mean duration of each family.
        mapping: dict
            Comprises the families and the encoded families.
        real_family_probs: dict
            Comprises the probabilities of the real families.
        real_dataset: dataframe
            Refers to the updated real dataset (maped families).

        """
        ticket_seasonality, family_seasonality, family_mean_duration = {}, {}, {}
        n_col = 1
        
        if is_database:   
            ### Change according to existing database
            cursor = connection.cursor()
            columns_to_read = ['ID', 'Subfamily', 'discovered_date', 'end_date', 'operator_action_timestamps']
            database_columns = ', '.join(list(map(str.lower, columns_to_read)))
            cursor.execute(f'SELECT {database_columns} FROM test_table')
            rows = cursor.fetchall()

            dataset = pd.DataFrame(rows, columns=columns_to_read)
            dataset.rename(columns={'operator_action_timestamps': 'Steps'}, inplace = True)
            dataset['Family'] = dataset['Subfamily'].apply(lambda x: x.split("-")[0])
        else:
            columns_to_read = ['ref_num', 'discovered_date', 'end_date', 'category', 'alert_code', 'time_stamp']
            filepath = "./Resources/Datasets/" + filename 
            if ".xlsx" in filename:
                dataset = pd.read_excel(filepath, usecols=columns_to_read, index_col=None)
            else:
                dataset = pd.read_csv(filepath, usecols=columns_to_read, index_col=None, sep=";")
            dataset.rename(columns={'ref_num': 'ID', 'category': 'Family', 'alert_code': 'Subfamily', 'time_stamp': 'Steps'}, inplace = True)

        dataset['ID'] = dataset['ID'].astype(np.int32)
        dataset['Family'] = dataset['Family'].astype("category")
        dataset['Subfamily'] = dataset['Subfamily'].astype("category")
        
        dataset.rename(columns={'raised': 'Raised (UTC)'}, inplace = True)
        dataset.rename(columns={'discovered_date': 'Raised (UTC)', 'end_date': 'Fixed'}, inplace = True)
        dataset = dataset.dropna(subset=['Steps', 'Family', 'Subfamily'], how= "all")
        
        dataset['Steps'] = dataset['Steps'].apply(Configurator.convert_timestamp_to_datetimelist)
        dataset = dataset[dataset['Steps'] != 0]
        print("length:", dataset.shape[0])
        
        temp_dict, dataset = Configurator.solve_family_anomalies(dataset)
        subfamilies_mean = Configurator.get_subfamilies_mean(dataset, temp_dict)
        dataset = Configurator.solve_timestamp_anomalies(dataset, temp_dict, subfamilies_mean)
        dataset["raised"] = pd.to_datetime(dataset['raised'], dayfirst=True)
        
        dataset.sort_values(by='raised', inplace=True)
        dataset['Year/month'] = dataset['raised'].apply(lambda x: datetime.strftime(x, '%m'))
        family_duration_distribution = dataset.groupby('Family')['Ticket Duration'].mean().reset_index(name="mean")
        family_duration_distribution['mean'] = family_duration_distribution['mean'].apply(lambda x: x*0.1)
        family_mean_duration = family_duration_distribution.set_index('Family')['mean'].to_dict()
        family_distribution = dataset.groupby(['Year/month', 'Family']).size().reset_index(name="Count")
        daily_tickets = dataset.groupby(dataset['raised'].dt.strftime('%m-%d')).size().reset_index(name='ticket_count')
        daily_tickets.columns = ['Month_day', 'Ticket_count']

        ticket_series = dataset['Year/month'].value_counts()
        ticket_series = ticket_series.sort_index()
        ticket_seasonality = Configurator.get_daily_probabibilies(len(dataset), daily_tickets)
        
        has_one_year_data, all_day_month_combinations = Configurator.check_real_dataset_completeness(dataset, daily_tickets)
        if not has_one_year_data:
            ticket_seasonality = Configurator.interpolate_missing_data(ticket_seasonality, all_day_month_combinations)
        
        for index, row in family_distribution.iterrows():    
            month = int(row["Year/month"])
            family = row["Family"]
            month_name = datetime(1900, month, 1).strftime('%B')
            if month_name not in family_seasonality.keys():
                family_seasonality[month_name] = {}
                family_seasonality[month_name][family] = 0
             
            ticket_number = ticket_series.get(key = row["Year/month"])
            family_seasonality[month_name][family] = row["Count"]/ticket_number
            
        all_families = dataset['Family'].unique()
        for l in family_seasonality.keys():
            for fam in all_families:
                if fam not in family_seasonality[l]:
                    family_seasonality[l][fam] = 0
                
        mapping = Utils.encode_families(list(dataset['Family'].unique()))
        real_family_probs, real_dataset = Configurator.plot_real_data(dataset, family_duration_distribution, n_col, mapping, show_real_data)

        return ticket_seasonality, family_seasonality, family_mean_duration, mapping, real_family_probs, real_dataset

    def check_real_dataset_completeness(dataset, daily_tickets):
        """
        Checks if the real dataset has missing data in terms of dates.

        Parameters
        ----------
        dataset : dataframe
            Real dataset.
        daily_tickets : dataframe
            Dataset with two columns (Month-day and ticket count).

        Returns
        -------
        bool
            Has or does not have one year full of data.
        all_day_month_combinations : list
            List of month-day combinations.

        """
        start_date = dataset['raised'].min()
        full_year_start_date = pd.Timestamp(year=start_date.year, month=1, day=1)
        #print("Full year start date:", full_year_start_date)
        full_year_end_date = pd.Timestamp(year=start_date.year, month=12, day=31)
        #print("Full year end date:", full_year_end_date)
        
        date_range = pd.date_range(start=full_year_start_date, end=full_year_end_date, freq="D")
        all_day_month_combinations = [date.strftime('%m-%d') for date in date_range]
        #print("All day combinations:", all_day_month_combinations)
        
        existing_day_months = daily_tickets['Month_day'].tolist()
        #print("Existing_day_months:", existing_day_months)
        missing_day_months = [day for day in all_day_month_combinations if day not in existing_day_months]

        if not missing_day_months:
            print("Dataset has one year worth of data")
            return True, all_day_month_combinations
        else:
            print("Dates missing:", missing_day_months)
            return False, all_day_month_combinations
        
    def interpolate_missing_data(ticket_seasonality, all_day_months):
        """
        Interpolates missing data using the iterative imputer (MICE).

        Parameters
        ----------
        ticket_seasonality : dict
            Comprises information about existing month-day combinations (prob and number of tickets).
        all_day_months : list
            List of month-day combinations.

        Returns
        -------
        Dataframe
            Updated dataframe with interpolated missing dates.

        """
        df = pd.DataFrame.from_dict(ticket_seasonality, orient='index').reset_index()
        df.columns = ['day_month', 'probability', 'ticket_count']
    
        full_df = pd.DataFrame({'day_month': list(all_day_months)})
        merged_df = full_df.merge(df, on='day_month', how='left')
        
        non_numeric = merged_df[['day_month']]
        numeric = merged_df[['probability', 'ticket_count']]
        
        imputer = IterativeImputer(max_iter=10, random_state=42)
        imputed_array = imputer.fit_transform(numeric)        
        merged_df = pd.concat([non_numeric, pd.DataFrame(imputed_array, columns=numeric.columns)], axis=1)
        
        return merged_df.set_index('day_month')['probability'].apply(lambda x: {'prob': x}).to_dict()

    def get_daily_probabibilies(dataset_size, daily_tickets):
        """
        Gets the probability of the tickets in each month-day.

        Parameters
        ----------
        dataset_size : int
            Size of the dataset.
        daily_tickets : TYPE
            Dataset with two columns (Month-day and ticket count).

        Returns
        -------
        ticket_seasonality : dict
            Comprises information about existing month-day combinations (prob and number of tickets).

        """

        ticket_seasonality = {}
        
        for row in daily_tickets.itertuples(index=False):
            ticket_seasonality[row.Month_day] = {}
            ticket_seasonality[row.Month_day]["prob"] = row.Ticket_count/dataset_size
            ticket_seasonality[row.Month_day]["n_tickets"] = row.Ticket_count

        return ticket_seasonality
    
    def plot_real_data(dataset, family_duration_distribution, n_col, mapping, plot_data):
        """
        Plots real families's frequency over the year

        Parameters
        ----------
        dataset : Dataframe
            Real dataset.
        family_duration_distribution : Dataframe
            Dataset containing the mean duration of each family
        n_col : int
            Column to read.
        mapping : dict
            Comprises the families and the encoded families.
        plot_data : bool
            Plot or not the real data patterns (mean family duration and family distribution).

        Returns
        -------
        family_probs_data : dict
            Comprises the probability of each real family.
        dataset : dataframe
            Updated real dataset.

        """
        inverse_mapping = {v: k for k, v in mapping.items()}
        dataset["Family"] = dataset["Family"].map(inverse_mapping)
        family_probs_data = dataset['Family'].value_counts(normalize=True).sort_index()
        
        if plot_data:
            freq = dataset.pivot_table(index="Year/month", columns="Family", aggfunc="size", fill_value=0)
        
            families = sorted(freq.columns)
            months = freq.index
            cumulative = np.zeros(len(months))
            freq = freq[families]
        
            a4_dims = (30, 12)
            fig, ax = plt.subplots(figsize=a4_dims)
            for family in families:
                plt.barh(months, freq[family], left=cumulative, label=family)
                cumulative += freq[family]
        
            plt.xlabel("Ticket Frequency")
            plt.ylabel("Months")
            plt.xlim(0, 830)
            plt.title("Stacked Horizontal Bar Chart of Family Frequency by Year/Month")
            plt.legend(fontsize = 24, bbox_to_anchor=(1.01, 0.5) , loc='center left', ncol= n_col, borderaxespad=0.,)
            plt.tight_layout()
            plt.savefig('Plots\\real_families_month.svg', format="svg")
            plt.show()
            
            a4_dims = (25, 12)
            fig, axs = plt.subplots(figsize=a4_dims)
            axs.bar(family_duration_distribution['Family'], family_duration_distribution['mean'])
            
            for tick in axs.get_xticklabels():
                tick.set_rotation(45)
                
            xticks_positions = np.arange(len(family_duration_distribution['Family']))
            xticks_labels = family_duration_distribution['Family']
            axs.set_xticks(xticks_positions)
            axs.set_xticklabels(xticks_labels, fontsize=10, ha='right')
        
            axs.set_title("Real Families Mean Duration")
            axs.set_xlabel("Timerange", fontsize=12)
            axs.set_ylabel("Time (seconds)", fontsize=12)
            plt.savefig('Plots\\real_mean_fix_duration.png', bbox_inches='tight')
            plt.show()
        
        return family_probs_data, dataset
        
    def get_suspicious_ips():
        """
        Gets the suspicious IPs.

        Returns
        -------
        suspicious_ips : dict
            Comprises information regarding suspicious IPs.

        """
        path = 'Resources/Ips/bad_ips.txt'
        print(f'Suspicious file Size is {os.stat(path).st_size / (1024 * 1024)} MB')
        suspicious_ips = {}
        with open(path) as infile:
            for line in infile:
                line_split = line.split("\t")
                suspicious_ips[line_split[0]] = line_split[1].rstrip()
                
        return suspicious_ips

    def instantiate_special_steps(max_transfer_steps):
        """
        Builds the special operations - initiate, end, and transfer.        

        Parameters
        ----------
        max_transfer_steps : int
            Maximum number of transfer steps.

        Raises
        ------
        ValueError
            if max_transfer_steps < 1.

        Returns
        -------
        special_steps : dict
            Comprises information about special steps.

        """
        special_steps = {}
        special_steps["init_opt"], special_steps["end_opt"], special_steps["transfer_opt"] = {}, {}, {}

        techniques_pool = string.ascii_letters + string.digits    
        #print("\nTechniques pool:", techniques_pool)
        init_techniques_pool = random.sample(techniques_pool, k = 2)
        #print("Initial techniques:", init_techniques_pool)
        end_techniques_pool = random.sample([tec for tec in techniques_pool if tec not in init_techniques_pool], k = 2)
        #print("End techniques:", end_techniques_pool)

        transfer_op = random.choice([tec for tec in techniques_pool if (tec not in init_techniques_pool and tec not in end_techniques_pool)])
            
        if max_transfer_steps < 1:
            raise ValueError("There must be transfer steps")
        else:
            special_steps["transfer_opt"][transfer_op] = random.randint(1, max_transfer_steps)
        
        subtechniques_used = []
        for i in init_techniques_pool:
            special_steps["init_opt"][i] = {}
            init_sup_opt = random.sample([tec for tec in techniques_pool if (tec not in init_techniques_pool and tec not in end_techniques_pool and tec != transfer_op and tec not in subtechniques_used)], k = 1)
            subtechniques_used.append(init_sup_opt[0])
            special_steps["init_opt"][i][init_sup_opt[0]] = random.randint(1, 3)

        for e in end_techniques_pool:
            special_steps["end_opt"][e] = {}
            end_sup_opt = random.sample([tec for tec in techniques_pool if (tec not in init_techniques_pool and tec not in end_techniques_pool and tec != transfer_op and tec not in subtechniques_used)], k = 1)
            subtechniques_used.append(end_sup_opt[0])
            special_steps["end_opt"][e][end_sup_opt[0]] = random.randint(1, 3)

        print("Special Operations:", special_steps)
        return special_steps