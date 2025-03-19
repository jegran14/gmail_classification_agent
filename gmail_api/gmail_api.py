import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from typing import Dict, List, Optional, Union


class GmailAPI:
    """A wrapper class for the Gmail API operations needed by the agent."""
    
    SCOPES = [
        'https://www.googleapis.com/auth/gmail.modify',
        'https://www.googleapis.com/auth/gmail.labels',
        'https://www.googleapis.com/auth/gmail.settings.basic'
    ]
    
    def __init__(self, credentials_path: str, token_path: str):
        """
        Initializes the GmailAPI object.
        
        Args:
            credentials_path (str): The path to the credentials file.
            token_path (str): The path to the token file.
        """
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.service = None
    
    def __call__(self):
        self.authenticate()
    
    # region AUTHENTICATION
    def authenticate(self) -> None:
        """Handle the OAth2 flow and build the Gmail service."""
        creds = None
        
        if os.path.exists(self.token_path):
            creds = Credentials.from_authorized_user_file(self.token_path)
            
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, self.SCOPES)
                creds = flow.run_local_server(port=0)
                
            with open(self.token_path, 'w') as token:
                token.write(creds.to_json())
                
        self.service = build('gmail', 'v1', credentials=creds)
    # endregion    
    
    # region LABELS
    def list_labels(self) -> Optional[List[Dict]]:
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
        try:
            return self.service.users().labels().list(userId='me').execute().get('labels', [])
        except Exception as error:
            print(f'An error occurred: {error}')
            return None
    
    def create_label(self, label_name: str, label_color: Optional[str] = None) -> Optional[Dict]:
        """
        Create a new label for the authenticated user.
        
        Args:
            label_name (str): The name of the label to create.
            label_color (str): The color of the label in hex format.
            
        Returns:
            Created label resource if successful, None otherwise.
        """
        try:
            label_content = {'name': label_name}
            if label_color:
                label_content['color'] = {
                    'backgroundColor': label_color,
                    'textColor': '#000000'  # Use 'white' as a predefined color name
                }
                
            return self.service.users().labels().create(
                userId='me', body=label_content).execute()
        except Exception as error:
            print(f'An error occurred: {error}')
            return None
        
    def delete_label(self, label_id: str) -> None:
        """
        Delete a label by its ID.
        
        Args:
            label_id (str): The ID of the label to delete.
        """
        try:
            self.service.users().labels().delete(userId='me', id=label_id).execute()
        except Exception as error:
            print(f'An error occurred: {error}')
    
    def get_label_id(self, label_name: str) -> Optional[str]:
        """
        Get the ID of a label by its name.
        
        Args:
            label_name (str): The name of the label to get the ID for.
            
        Returns:
            The ID of the label if found, None otherwise.
        """
        try:
            labels = self.service.users().labels().list(userId='me').execute().get('labels', [])
            for label in labels:
                if label['name'] == label_name:
                    return label['id']
        except Exception as error:
            print(f'An error occurred: {error}')
            return None

    def update_label(self, label_id: str, new_name: Optional[str] = None, new_color: Optional[str] = None) -> Optional[Dict]:
        """
        Update an existing label's name and/or color.
        
        Args:
            label_id (str): The ID of the label to update.
            new_name (str): The new name for the label.
            new_color (str): The new color for the label in hex format.
            
        Returns:
            Updated label resource if successful, None otherwise.
        """
        try:
            label_content = {}
            if new_name:
                label_content['name'] = new_name
            if new_color:
                label_content['color'] = {
                    'backgroundColor': new_color,
                    'textColor': '#000000'  # Use 'black' as a predefined color name
                }
                
            return self.service.users().labels().patch(
                userId='me', id=label_id, body=label_content).execute()
        except Exception as error:
            print(f'An error occurred: {error}')
            return None
    # endregion
    
    
    # region FILTERS
    def list_filters(self) -> Optional[List[Dict]]:
            """
            List all filters for the authenticated user.
            
            Returns:
                List of filter resources if successful, None otherwise.
            """
            try:
                return self.service.users().settings().filters().list(userId='me').execute().get('filter', [])
            except Exception as error:
                print(f'An error occurred: {error}')
                return None
            
            
    def create_filter(self, criteria: Dict[str, str], actions: Dict[str, Union[str, List[str]]]) -> Optional[Dict]:
        """
        Create a GMail filter that automatically applies a label to matching messages
        
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

            
        Returns:
            Created filter resource if successful, None otherwise.
        """
        try:
            # Ensure addLabelIds and removeLabelIds are strings
            if 'addLabelIds' in actions and isinstance(actions['addLabelIds'], list):
                actions['addLabelIds'] = ','.join(actions['addLabelIds'])
            if 'removeLabelIds' in actions and isinstance(actions['removeLabelIds'], list):
                actions['removeLabelIds'] = ','.join(actions['removeLabelIds'])
            
            filter_content = {
                'criteria': criteria,
                'action': actions
            }
                
            return self.service.users().settings().filters().create(
                userId='me', body=filter_content).execute()
                
        except Exception as error:
            print(f'An error occurred: {error}')
            return None
            
            
    def delete_filter(self, filter_id: str) -> None:
        """
        Delete a filter by its ID.
        
        Args:
            filter_id (str): The ID of the filter to delete.
        """
        try:
            self.service.users().settings().filters().delete(userId='me', id=filter_id).execute()
        except Exception as error:
            print(f'An error occurred: {error}')
            
    def update_filter(self, filter_id: str, criteria: Optional[Dict[str, str]] = None, actions: Optional[Dict[str, Union[str, List[str]]]] = None) -> Optional[Dict]:
        """
        Update an existing filter's criteria and/or actions. 
        To update a filter, we are deleting the previous one an creating a new one adding the new criteria and actions.
        
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
        self.delete_filter(filter_id)
        return self.create_filter(criteria, actions)
        
    # endregion
        
def main():
    '''
    TODO: 
        - Need to make a separate class to handle the tests
    '''
    credentials_path = 'gmail_api/utils/credentials.json'
    token_path = 'gmail_api/utils/token.json'
    
    gmail_api = GmailAPI(credentials_path, token_path)
    gmail_api.authenticate()
    
    try:
        # Test list_labels
        labels = gmail_api.list_labels()
       # print(labels)   
        
        # Test create_label
        label_name = 'Test Label'
        label_color = '#000000'
        label = gmail_api.create_label(label_name, label_color)
        print(label)
        
        # Test delete label
        label_id = label['id']
        gmail_api.delete_label(label_id)     
        
    except HttpError as error:
        print(f'An error occurred: {error}')
        
if __name__ == '__main__':
    main()