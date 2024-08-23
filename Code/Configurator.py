from Code.Utils import Utils
from PyQt5.QtWidgets import QFileDialog
import os, string, random, ruamel.yaml, ijson
import pandas as pd
from datetime import datetime
import pendulum
import numpy as np

class Configurator:
    
    # Checks if the configuration file path exists
    def check_configuration_path(domain):
        
        path = f'Configurations/{domain}/Init_cfg.yaml'
        if os.path.exists(path):
            return True
    
    # Reads the configuration file
    def read_configuration_file(domain, path):
        
        config_data = {}
        try:
            with open(path, "r") as fh:
                config_data = ruamel.yaml.load(fh, Loader=ruamel.yaml.RoundTripLoader)
                return config_data
        except FileNotFoundError:
            print("Couldn't find configuration file!" )
            
    # Checks if param exists in configuration file 
    def check_param_in_config(config, param):

        if param in config.keys():
            return True
        else:
            print(f'The config does not have the param {param}')
    
    # Loads several parameters from the configuration file
    def load_configurations(domain):

        path =  f'Configurations/{domain}/Init_cfg.yaml'
        config_data = Configurator.read_configuration_file(domain, path)
        #print("Config:", config_data)
        interface_params, generation_params, treatment_params = {}, {}, {}
        generation_params["suspicious_countries"] = {}
        
        interface_params["multiple_attack_selector"], interface_params["outlier_selector"], interface_params["suspicious_selector"] = False, True, True
        generation_params["ip_selected_idx"], generation_params["format_selected_idx"] = 0, 0
        generation_params["family_selection"] = "Random"
        generation_params["ip_selector"], generation_params["ticket_seasonality_selector"], generation_params["family_seasonality_selector"], generation_params["techniques_seasonality_selector"], generation_params["ticket_escalation_selector"], generation_params["ticket_growth_selector"] = True, True, True, False, True, True
        treatment_params["ticket_similarity_selector"], treatment_params["ticket_verification_selector"] = True, True

        growth_operations = ["increase", "maintain", "decrease"]
            
        try:
            interface_params["generation_mode"] = config_data["generation_parameters"]["generation_mode"]
            
            generation_params['train_ticket'] = config_data["generation_parameters"]['train_ticket']
            generation_params['test_ticket'] = config_data["generation_parameters"]['test_ticket']
            generation_params['ticket_growth_type'] = config_data["generation_parameters"]['ticket_growth_type']
            generation_params['ticket_growth_rate'] = config_data["generation_parameters"]['ticket_growth_rate']
            generation_params['families_number'] = config_data["generation_parameters"]['families_number']
            generation_params['minsubfamilies_number'] = config_data["generation_parameters"]['minsubfamilies_number']
            generation_params['maxsubfamilies_number'] = config_data["generation_parameters"]['maxsubfamilies_number']
            generation_params['techniques_number'] = config_data["generation_parameters"]['techniques_number']
            generation_params['minsubtechniques_number'] = config_data["generation_parameters"]['minsubtechniques_number']
            generation_params['maxsubtechniques_number'] = config_data["generation_parameters"]['maxsubtechniques_number']
            generation_params['seed'] = config_data["generation_parameters"]['seed']
            generation_params["start_date"] = config_data["generation_parameters"]["start_date"]
            generation_params["end_date"] = config_data["generation_parameters"]["end_date"]
            generation_params["test_timerange"] = config_data["generation_parameters"]["test_timerange"]
            generation_params["outlier_rate"] = config_data["generation_parameters"]['outlier_rate']
            generation_params["outlier_cost"] = config_data["generation_parameters"]['outlier_cost']
            generation_params["escalate_rate_percentage"] = config_data["generation_parameters"]['escalate_rate_percentage']
            generation_params["family_rate_percentage"] = config_data["generation_parameters"]['family_rate_percentage']
            generation_params["subfamily_rate_percentage"] = config_data["generation_parameters"]['subfamily_rate_percentage']
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
            generation_params["prioritize_lower_teams"] = config_data["generation_parameters"]["prioritize_lower_teams"]
            generation_params["reset_analysts_data"] = config_data["generation_parameters"]["reset_analysts_data"]
            generation_params["balanced_shifts"] = config_data["generation_parameters"]["balanced_shifts"]
            generation_params["debug"] = config_data["generation_parameters"]["debug"]
            generation_params["logger_active"] = config_data["generation_parameters"]["logger_active"]
            generation_params["print_plots"] = config_data["generation_parameters"]["print_plots"]
            generation_params["use_default_family"] = config_data["generation_parameters"]["use_default_family"]
            generation_params["time_equal_probabilities"] = config_data["generation_parameters"]["time_equal_probabilities"]
            generation_params["week_equal_probabilities"] = config_data["generation_parameters"]["week_equal_probabilities"]
            generation_params["max_priority_levels"] = config_data["generation_parameters"]["max_priority_levels"]
            generation_params["action_operations"] = config_data["action_operations"]
            generation_params["ips_pool"] = config_data["ips_pool"]
            generation_params["default_alert_pool"] = config_data["families"]
            generation_params["family_time_4h"] = config_data["family_time_4h"]
            generation_params["week_time"] = config_data["week_time"]
            generation_params["analysts_skills"] = config_data["analysts_info"]
            generation_params["teams_frequency"] = config_data["teams_freq"]
            
            treatment_params["day_stages"] = config_data["day_stages"]
            treatment_params["shifts"] = config_data["shifts"]
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
            
        if generation_params['ticket_growth_type'] not in growth_operations:
            raise ValueError(f"Invalid ticket growth operation! Options are {growth_operations}")
        
        print("Cybersecurity configuration file successfully loaded!") 
        print(suspicious_countries)

        return interface_params, generation_params, treatment_params, suspicious_countries
        
    # Updates the configuration file
    def update_configuration_data(param, content, domain, path):

        config_data = Configurator.read_configuration_file(domain, path)
        config_data[param].update(content)
        
        with open(path, 'w') as f:
            ruamel.yaml.dump(config_data, f, Dumper=ruamel.yaml.RoundTripDumper)
        print(f'{domain} custom configuration saved!')

    # Reads a particular part of the configuration file
    def read_configuration_section(domain, section):
        
        path = f'Configurations/{domain}/Init_cfg.yaml'
        config_data = Configurator.read_configuration_file(domain, path)
        
        return config_data[section] 
                 
    # Shows a QFileDialog window and picks the configuration file
    def load_configuration_data(window, path):
        
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        filename, _ = QFileDialog.getOpenFileName(window, "Open File", path, "", options=options)
        return filename
    
    # Shows a QFileDialog window and stores the configuration file
    def save_dialog(window):
        
        options = QFileDialog.Options()
        filename, _ = QFileDialog.getSaveFileName(window, 'Save as... File', 'Custom_cfg', filter="YAML (*.yaml)",options=options)
        return filename
    
    # Stores the configurations set by the user
    def save_new_config_file(domain, param, content, new_file):
    
        path =  f'Configurations/{domain}/Init_cfg.yaml'
        config_data = Configurator.read_configuration_file(domain, path)
        
        config_data[param].update(content)
        with open(new_file, 'w') as f:
            ruamel.yaml.dump(config_data, f, Dumper=ruamel.yaml.RoundTripDumper)
            
        print("New configuration file saved!")
    
    # Gets the countries and their IPs
    def get_countries_data(path, countries_picked):
        
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
    
    # Gets the names of the countries
    def get_countries_names(path):
        
        countries = []
        with open(path, "rb") as f:
            for countries_data in ijson.items(f, "countries"):
                countries = list(countries_data.keys())
        #print("Countries:", countries)
        return countries

    # Fixes null families and subfamilies
    def solve_family_anomalies(dataset):
        
        incidents_info = dataset.groupby(['Family', 'Subfamily']).size()
        #print(incidents_info)

        families_info = {}
        for incident_data, count in incidents_info.items():
            if count != 0:
                family = incident_data[0]
                subfamily = incident_data[1]
                if family not in families_info:
                    families_info[family] = []
                if incident_data not in families_info[family]:
                    families_info[family].append(subfamily)
        test_dict = dataset.to_dict("index")

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
    
    # Converts timestamps into pendulum instances
    def convert_timestamps(list_):
        
        temp = []
        #print("list:", list_)
        if len(list_) != 1:
            for k in list_:
                try:
                    #print(k)
                    dt_object = pendulum.from_timestamp(int(float(k)))
                    temp.append(dt_object.replace(tzinfo=None))
                except:
                    return []
        return temp
    
    # Checks null and timestamp format 
    def convert_timestamp_to_datetimelist(timestamps):
        
        #print(timestamps)
        if pd.isnull(timestamps):
            result = -1
        else:
            result = timestamps.replace('[', '')
            result = result.replace(']', '')
            result = result.split(', ')
            result = Configurator.convert_timestamps(result)
            if not result:
                print("Entry removed!")
                #print(result)
                result = 0
        return result
    
    # Fixes null timestamps
    def solve_timestamp_anomalies(dataset, temp_dict, subfamilies_mean):

        ticket_durations = []
        raised = []

        #temp_dict = dataset.to_dict("index")
        for i in temp_dict:
            if temp_dict[i]['Steps'] == -1:
                #print(temp_dict[i])
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
    
    # Gets the duration of a ticket
    def get_ticket_duration(start, end, subfamily):
        
        time_diff = end - start
        minutes = round(time_diff.total_seconds() / 60)
        return minutes
    
    # Gets the mean of each subfamily
    def get_subfamilies_mean(dataset, temp_dict, without_nan):

        subfamilies_mean = {}
        all_subfamilies = dataset['Subfamily'].unique()
        all_subfamilies = [item for item in all_subfamilies if not(pd.isnull(item)) == True]
        min_init_date = pendulum.datetime(2100, 6, 1).replace(tzinfo=None)
        
        for i in temp_dict:
            if temp_dict[i]["Steps"] != -1:
                #print("Aqui")
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
            #print("Subfamily:", subfamilies_mean[subfamily])
            avg += subfamilies_mean[subfamily]["time_spent"] /subfamilies_mean[subfamily]["count"]

        avg = avg/len(subfamilies_mean)
        for sub in all_subfamilies:
            if sub not in subfamilies_mean:
                subfamilies_mean[subfamily] = {}
                subfamilies_mean["time_spent"] = avg
                subfamilies_mean["count"] = 1
               
        #print("Subfamilies mean:", subfamilies_mean)
        return subfamilies_mean
        
    # Gets the seasonality of the real dataset. The seasonality of each family over the year is converted in probability weights
    # Beware that the real dataset should be processed and cleaned
    def get_ticket_seasonality(source, file, connection):
        
        ticket_seasonality, family_seasonality, family_mean_duration = {}, {}, {}
        
        if source == "DATABASE":   
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
            if ".xlsx" in file:
                dataset = pd.read_excel(file, usecols=columns_to_read, index_col=None)
            else:
                dataset = pd.read_csv(file, usecols=columns_to_read, index_col=None, sep=";")
            dataset.rename(columns={'ref_num': 'ID', 'category': 'Family', 'alert_code': 'Subfamily', 'time_stamp': 'Steps'}, inplace = True)
            dataset = dataset[(dataset['ID'] != "ethernet1/2")]

        dataset['Family'] = dataset['Family'].astype("category")
        dataset['ID'] = dataset['ID'].astype(np.int32)
        dataset['Subfamily'] = dataset['Subfamily'].astype("category")
        print("Dataset Size:", dataset.shape[0])    
        dataset.rename(columns={'discovered_date': 'Raised (UTC)', 'end_date': 'Fixed'}, inplace = True)
        dataset = dataset.dropna(subset=['Steps', 'Family', 'Subfamily'], how= "all")
        
        dataset['Steps'] = dataset['Steps'].apply(Configurator.convert_timestamp_to_datetimelist)
        #print("length:", dataset.shape[0])
        dataset = dataset[dataset['Steps'] != 0]
        
        temp_dict, dataset = Configurator.solve_family_anomalies(dataset)
        subfamilies_mean = Configurator.get_subfamilies_mean(dataset, temp_dict, False)
        dataset = Configurator.solve_timestamp_anomalies(dataset, temp_dict, subfamilies_mean)
        dataset["raised"] = pd.to_datetime(dataset['raised'], dayfirst=True)
        
        dataset.sort_values(by='raised', inplace=True)
        dataset['Year/month'] = dataset['raised'].apply(lambda x: datetime.strftime(x, '%m'))
        family_duration_distribution = dataset.groupby('Family')['Ticket Duration'].mean().reset_index(name="mean")
        #print("Original Mean Time spent:", family_duration_distribution)
        family_duration_distribution['mean'] = family_duration_distribution['mean'].apply(lambda x: x*0.1)
        #print("Real Scaled Mean Time spent:", family_duration_distribution)
        family_mean_duration = family_duration_distribution.set_index('Family')['mean'].to_dict()
        #print("Mean duration:", family_mean_duration)

        family_distribution = dataset.groupby(['Year/month', 'Family']).size().reset_index(name="Count")
        ticket_seasonality["high_season"], ticket_seasonality["off_season"] = {}, {}
        ticket_seasonality["high_season"]["ticket"], ticket_seasonality["off_season"]["ticket"] = 0, 0
        
        ticket_series = dataset['Year/month'].value_counts()

        ticket_seasonality = Configurator.get_high_low_seasonlity(len(dataset), ticket_series, ticket_seasonality)
        #print(family_distribution)
        
        for index, row in family_distribution.iterrows():    
            month = int(row["Year/month"])
            family = row["Family"]
            month_name = datetime(1900, month, 1).strftime('%B')
            if month_name not in family_seasonality.keys():
                family_seasonality[month_name] = {}
                family_seasonality[month_name][family] = 0
             
            ticket_number = ticket_series.get(key = row["Year/month"])
            family_seasonality[month_name][family] = row["Count"]/ticket_number
        
        #print("Dataset size:", dataset.shape[0])
        all_families = dataset['Family'].unique()
        for l in family_seasonality.keys():
            #print("Month", l)
            for fam in all_families:
                if fam not in family_seasonality[l]:
                    family_seasonality[l][fam] = 0
                
        mapping = Utils.encode_families(list(dataset['Family'].unique()))

        return ticket_seasonality, family_seasonality, family_mean_duration, mapping
    
    # Gets High and Low season in term of ticket volume
    def get_high_low_seasonlity(dataset_size, ticket_series, ticket_seasonality):
        
        ranked_months = ticket_series.rank(method='first')
        #print(ranked_months)
        median_rank = ranked_months.median()
        
        high_seasonality_months = sorted(ranked_months[ranked_months > median_rank].index.tolist())
        #print("High months:", high_seasonality_months)
        #print("N tickets in High months:", ticket_series[high_seasonality_months].sum())
        low_seasonality_months = sorted(ranked_months[ranked_months <= median_rank].index.tolist())
        #print("Low months:", low_seasonality_months)
        #print("N tickets in High months:", ticket_series[low_seasonality_months].sum())
        
        ticket_seasonality["off_season"]["ticket"] = ticket_series[low_seasonality_months].sum()
        ticket_seasonality["high_season"]["ticket"] = ticket_series[high_seasonality_months].sum()
        ticket_seasonality["off_season"]["months"] = [int(month) for month in low_seasonality_months]
        ticket_seasonality["high_season"]["months"] = [int(month) for month in high_seasonality_months]
        ticket_seasonality["off_season"]["prob"] = ticket_seasonality["off_season"]["ticket"]/dataset_size  
        ticket_seasonality["high_season"]["prob"] = ticket_seasonality["high_season"]["ticket"]/dataset_size
        
        return ticket_seasonality
        
    # Gets the suspicious IPs
    def get_suspicious_ips():
        path = 'Resources/Ips/bad_ips.txt'
        print(f'Suspicious file Size is {os.stat(path).st_size / (1024 * 1024)} MB')
        suspicious_ips = {}
        with open(path) as infile:
            for line in infile:
                line_split = line.split("\t")
                suspicious_ips[line_split[0]] = line_split[1].rstrip()
                
        return suspicious_ips

    # Gets the special operations - initiate, end, and transfer
    def get_special_steps(n_transfer_steps):
        
        special_steps = {}
        special_steps["init_opt"], special_steps["end_opt"], special_steps["transfer_opt"] = {}, {}, {}

        techniques_pool = string.ascii_letters + string.digits    
        #print("\nTechniques pool:", techniques_pool)
        init_techniques_pool = random.sample(techniques_pool, k = 2)
        #print("Initial techniques:", init_techniques_pool)
        end_techniques_pool = random.sample([tec for tec in techniques_pool if tec not in init_techniques_pool], k = 2)
        #print("End techniques:", end_techniques_pool)

        transfer_op = random.choice([tec for tec in techniques_pool if (tec not in init_techniques_pool and tec not in end_techniques_pool)])
            
        if n_transfer_steps < 1:
            raise ValueError("There must be transfer steps")
        else:
            special_steps["transfer_opt"][transfer_op] = random.randint(1, n_transfer_steps)
            #print("Special techniques techniques:", special_steps)
        
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
        
    # Reads the train and test datasets
    def read_generated_datasets(path):
        
        gen_id = Utils.get_most_recent_generation_id(path)
        print("Generation id found:", gen_id)
    
        if gen_id != None:
            files = os.listdir(path)
            filename = f'trainDataset_{gen_id}'
            matching_files = [file for file in files if file.startswith(filename)]
            file_extensions = [os.path.splitext(file)[1] for file in matching_files]
            #print("File extensions:", file_extensions)
            
            training_data_path = f'{path}trainDataset_{gen_id}{file_extensions[0]}'
            test_data_path = f'{path}testDataset_unsolved_{gen_id}{file_extensions[0]}'
            
            if file_extensions[0] == ".csv":
                train_df = pd.read_csv(training_data_path, sep=";")
                test_df = pd.read_csv(test_data_path, sep=";")
            else:
                train_df = pd.read_excel(training_data_path)
                test_df = pd.read_excel(test_data_path)
                
            train_df = Utils.process_dataset(train_df, True)
            test_df = Utils.process_dataset(test_df, False)
            return train_df, test_df, gen_id
        else:
            print("No Training and Test files were found")
            return pd.DataFrame(), pd.DataFrame(), gen_id