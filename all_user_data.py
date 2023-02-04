import os
import pandas as pd


class allUserData:

    def __init__(self, folder: str):
        """
        init class
        :param folder: str, folder name data
        """
        self.folder = folder
        self.list_data = list(os.listdir(folder))

    def joint_data(self):
        """
        This function joint data from query front
        :return: json, with data joint
        """
        all_data = pd.DataFrame()
        for file in self.list_data:
            temp_file = pd.read_csv(f"{self.folder}/{file}")
            all_data = pd.concat([all_data, temp_file])
            os.remove(f"{self.folder}/{file}")

        all_data = all_data.drop(columns=[all_data.columns[0]])
        all_data = all_data.reset_index(drop=True)

        json_data = all_data.to_json(orient='columns')

        return json_data
