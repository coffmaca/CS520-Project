import email
import pandas as pd

# Network analysis
import networkx as nx

def get_text_from_email(msg):
    """To get the content from email objects"""
    parts = []
    for part in msg.walk():
        if part.get_content_type() == 'text/plain':
            parts.append( part.get_payload() )
    return ''.join(parts)


def split_email_addresses(line):
    """To separate multiple email addresses"""
    if line and isinstance(line, str):
        addrs = line.split(',')
        addrs = list(map(lambda x: x.strip(), addrs))
    else:
        addrs = None
    return addrs


def compile_unique_recipients(line):
    """To compile unique recipients"""
    if line and isinstance(line, list):
        return line
    else:
        return []


def count_recipients(line):
    """To count and record the number of recipients"""
    count = 0
    if line and isinstance(line, list):
        count += len(line)

    return count


def compute_weighted_email_df(emails_df):
    """To compute weighted email dataframe"""
    new_rows = []

    for row in emails_df.iterrows():
        sender = row[1]['From'][0]
        rec_count = row[1]['Recipient_Count']

        to_set = set(row[1]['To']) if isinstance(row[1]['To'], list) else set()
        cc_set = set(row[1]['Cc']) if isinstance(row[1]['Cc'], list) else set()
        bcc_set = set(row[1]['Bcc']) if isinstance(row[1]['Bcc'], list) else set()

        for recipient in row[1]['Recipients']:
            if recipient in to_set:
                base_weight = 3
            elif recipient in cc_set:
                base_weight = 2
            elif recipient in bcc_set:
                base_weight = 1
            else:
                continue  # Skip if recipient isn't found in any of the 3 lists

            weight = base_weight / rec_count

            new_rows.append({
                'Sender': sender,
                'Recipient': recipient,
                'Weight': weight
            })

    new_df = pd.DataFrame(new_rows)

    new_df = new_df.groupby(['Sender', 'Recipient'], as_index=False)['Weight'].sum()

    return new_df


def ingest_csv(file_path):
    # Load emails
    emails_df = pd.read_csv(file_path)

    # Parse the emails into a list email objects
    messages = list(map(email.message_from_string, emails_df['message']))
    emails_df.drop('message', axis=1, inplace=True)

    # Get fields from parsed email objects
    keys = messages[0].keys()
    for message in messages:
        keys = message.keys()
        if "Cc" in keys and "Bcc" in keys:
            break
    for key in keys:
        emails_df[key] = [doc[key] for doc in messages]

    # Parse content from emails
    emails_df['content'] = list(map(get_text_from_email, messages))

    # Split multiple email addresses
    emails_df['From'] = emails_df['From'].map(split_email_addresses)
    emails_df['To'] = emails_df['To'].map(split_email_addresses)
    emails_df['Cc'] = emails_df['Cc'].map(split_email_addresses)
    emails_df['Bcc'] = emails_df['Bcc'].map(split_email_addresses)

    # Tally unique recipients
    emails_df["Recipients"] = emails_df[["To", "Cc", "Bcc"]].apply(
        lambda row: list(set().union(*map(compile_unique_recipients, row))),
        axis=1
    )
    emails_df["Recipient_Count"] = emails_df["Recipients"].map(len)

    # Extract the root of 'file' as 'user'
    emails_df['user'] = emails_df['file'].map(lambda x: x.split('/')[0])
    del messages

    # Set index and drop columns
    emails_df = emails_df.set_index('Message-ID').drop([
        'file',
        'Mime-Version',
        'Content-Type',
        'Content-Transfer-Encoding',
        'Subject',
        'X-From',
        'X-To',
        'X-cc',
        'X-bcc',
        'X-Folder',
        'X-Origin',
        'X-FileName',
        'content',
        'user'
    ], axis=1)

    # Parse datetime
    emails_df['Date'] = pd.to_datetime(emails_df['Date'], utc=True)  # , infer_datetime_format=True)

    return emails_df


def main(file_path: str, save_df: bool = True):
    if file_path == "data/emails.csv":
        emails_df = ingest_csv(file_path)
        if save_df:
            emails_df.to_pickle('data/emails_preprocessed.pkl')
    elif file_path == "data/emails_preprocessed.pkl":
        emails_df = pd.read_pickle(file_path)
        weighted_emails_df = compute_weighted_email_df(emails_df)
    elif file_path == "data/weighted_emails_df.pkl":
        weighted_emails_df = pd.read_pickle(file_path)

    # TODO - Filter (i) senders / recipients without "Enron" in address and (ii) emails with same sender / recipient.

    print("")


if __name__ == '__main__':
    emails_path = "data/emails.csv"
    emails_df_path = "data/emails_preprocessed.pkl"
    weighted_emails_df_path = "data/weighted_emails_df.pkl"
    main(emails_path)