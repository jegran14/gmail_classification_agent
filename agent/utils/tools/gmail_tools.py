from langchain_core.tools.convert import tool
from typing import Dict, Union, List, Optional

import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from gmail_api.gmail_api import GmailAPI

class GmailToolkit:
    def __init__(self):
        self.gmail_api = GmailAPI(credentials_path=os.getenv("GMAIL_CREDENTIALS_PATH"), token_path=os.getenv("GMAIL_TOKEN_PATH"))
        self.gmail_api() #Initialize API
        
        self._tools = [
            self.list_labels,
            self.create_label,
            self.delete_label,
            self.update_label,
            self.list_filters,
            self.create_filter,
            self.delete_filter,
            self.update_filter
        ]

    def get_tools(self):
        """Return the list of tools."""
        return [tool()(t.__get__(self, self.__class__)) for t in self._tools]

    def list_labels(self) -> str:
        """
        List all the labels in the user's gmail account.
        
        Returns:
            A list of dictionaries containing the label information.
            {
                "id": string,
                "name": string,
                "messageListVisibility": enum (MessageListVisibility),
                "labelListVisibility": enum (LabelListVisibility),
                "type": enum (Type),
                "messagesTotal": integer,
                "messagesUnread": integer,
                "threadsTotal": integer,
                "threadsUnread": integer,
                "color": {
                    object (Color)
                }
            }
        """
        labels = self.gmail_api.list_labels()
        
        if not labels:
            return "No labels found."
        return labels

    def create_label(self, label_name: str, label_color: str) -> str:
        """Create a new label in the user's gmail account.
        
        Args:
            label_name (str): The name of the label to create. You can nest labels by using a '/' in the name. example ParentLabel/ChildLabel
            label_color (str): The color of the label in hex format.
                List of background available colors: #000000, #434343, #666666, #999999, #cccccc, #efefef, #f3f3f3, #ffffff, #fb4c2f, #ffad47, #fad165, #16a766, #43d692, #4a86e8, #a479e2, #f691b3, #f6c5be, #ffe6c7, #fef1d1, #b9e4d0, #c6f3de, #c9daf8, #e4d7f5, #fcdee8, #efa093, #ffd6a2, #fce8b3, #89d3b2, #a0eac9, #a4c2f4, #d0bcf1, #fbc8d9, #e66550, #ffbc6b, #fcda83, #44b984, #68dfa9, #6d9eeb, #b694e8, #f7a7c0, #cc3a21, #eaa041, #f2c960, #149e60, #3dc789, #3c78d8, #8e63ce, #e07798, #ac2b16, #cf8933, #d5ae49, #0b804b, #2a9c68, #285bac, #653e9b, #b65775, #822111, #a46a21, #aa8831, #076239, #1a764d, #1c4587, #41236d, #83334c #464646, #e7e7e7, #0d3472, #b6cff5, #0d3b44, #98d7e4, #3d188e, #e3d7ff, #711a36, #fbd3e0, #8a1c0a, #f2b2a8, #7a2e0b, #ffc8af, #7a4706, #ffdeb5, #594c05, #fbe983, #684e07, #fdedc1, #0b4f30, #b3efd3, #04502e, #a2dcc1, #c2c2c2, #4986e7, #2da2bb, #b99aff, #994a64, #f691b2, #ff7537, #ffad46, #662e37, #ebdbde, #cca6ac, #094228, #42d692, #16a765
            
        Returns:
            A message indicating the success or failure of the label creation
            
        Tips:
            - If the user provides a label name with a '/', the label will be nested under the parent label.
            - If the user provides a label name that already exists, the label will not be created.
            - If the user provides a label color in natural language, you choose the closest color from the list of available colors.
        """
        label = self.gmail_api.create_label(label_name, label_color)
        if not label:
            return "Label could not be created."
        return f"Label {label['name']} created successfully."

    def delete_label(self, label_id: str) -> str:
        """Delete a label from the user's gmail account.
        
        Args:
            label_id (str): The ID of the label to delete.
            
        Returns:
            A message indicating the success or failure of the label deletion
            
        Tips:
            - If the user does not provide the label_id you can find it by listing all labels and finding the label by name.
            - After deleting the label, list labels to check that it has been correctly deleted.

        """
        try:
            self.gmail_api.delete_label(label_id)
            return f"Label with ID {label_id} deleted successfully."
        except Exception as error:
            return f"An error occurred: {error}"

    def update_label(self, label_id: str, new_name: Optional[str] = None, new_color: Optional[str] = None) -> str:
        """Update an existing label in the user's gmail account.
        
        Args:
            label_id (str): The ID of the label to update.
            new_name (str): The new name for the label.
            new_color (str): The new color for the label in hex format.
            
        Returns:
            A message indicating the success or failure of the label update.
            
        Tips:
            - If the user provides a label color in natural language, you choose the closest color from the list of available colors
            - If the user does not provide the label_id you can find it by listing all labels and finding the label by name.
        """        
        label = self.gmail_api.update_label(label_id, new_name, new_color)
        if not label:
            return "Label could not be updated."
        return f"Label {label['name']} updated successfully."

    def list_filters(self) -> str:
        """List all the filters in the user's gmail account.
        
        Returns:
            A list of dictionaries containing the filter information.
            {
                "id": string,
                "criteria": {
                    object (FilterCriteria)
                },
                "action": {
                    object (FilterAction)
                }
            }
            
        Formatting:
            - Display the filter criteria and actions in a human-readable format.
            - The user does not know the Label IDs, so you should display the label names instead.
        """
        return self.gmail_api.list_filters()

    def create_filter(self, criteria: Dict[str, str], actions: Dict[str, Union[str, List[str]]]) -> str:
        """Create a new filter in the user's gmail account.
        
        Args:
            criteria (Dict[str, str]): Filter criteria dictionary with possible keys:
                    - from: Sender email
                    - to: Recipient email
                    - subject: Email subject
                    - query: Gmail search query
            actions (Dict[str, Union[str, List[str]]]): Filter actions dictionary with possible keys:
                - addLabelIds: List of label IDs to add to the matching messages. Can only have one user defined label.
                - removeLabelIds: List of label IDs to remove from the matching messages.
                - forward: Email address to forward the matching messages to.

        Example:
        label_id_toAdd = "IMPORTANT" # User defined labels need to be passed by their id
        label_id_toRemove = "INBOX"
        filter_content = {
            "criteria": {"from": "gsuder1@workspacesamples.dev"},
            "action": {
                "addLabelIds": [label_id],
                "removeLabelIds": ["label_id"],
            },
        }
        """
        if 'addLabelIds' in actions and isinstance(actions['addLabelIds'], list):
            actions['addLabelIds'] = ','.join(actions['addLabelIds'])
        if 'removeLabelIds' in actions and isinstance(actions['removeLabelIds'], list):
            actions['removeLabelIds'] = ','.join(actions['removeLabelIds'])
        return self.gmail_api.create_filter(criteria, actions)
    
    def delete_filter(self, filter_id: str) -> str:
        """Delete a filter from the user's gmail account.
        
        Args:
            filter_id (str): The ID of the filter to delete.
            
        Returns:
            A message indicating the success or failure of the filter deletion
            
        Tips:
            - If the user does not provide the filter_id you can find it by listing all filters and finding the filter by criteria.
            - After deleting the filter, list filters to check that it has been correctly deleted.
        """
        try:
            self.gmail_api.delete_filter(filter_id)
            return f"Filter with ID {filter_id} deleted successfully."
        except Exception as error:
            return f"An error occurred: {error}"
        
    def update_filter(self, filter_id: str, criteria: Dict[str, str], actions: Dict[str, Union[str, List[str]]]) -> str:
        """
        Update an existing filter's criteria and/or actions.
        
        Args:
            filter_id (str): The ID of the filter to update.
            criteria (Dict[str, str]): Filter criteria dictionary with possible keys:
                - from: Sender email
                - to: Recipient email
                - subject: Email subject
                - query: Gmail search query
            actions (Dict[str, Union[str, List[str]]]): Filter actions dictionary with possible keys:
                - addLabelIds: List of label IDs to add to the matching messages. Can only have one user defined label.
                - removeLabelIds: List of label IDs to remove from the matching messages.
                - forward: Email address to forward the matching messages to.
                
        Returns:
            Updated filter resource if successful, None otherwise.
        """
        return "To update a filter you need to delete the existing filter and create a new one with the updated criteria and actions."
