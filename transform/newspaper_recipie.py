import argparse
import hashlib
import nltk
from nltk.corpus import stopwords
import logging
logging.basicConfig(level=logging.INFO)
from urllib.parse import urlparse

import pandas as pd

logger = logging.getLogger(__name__)

def main(filename):
	logger.info('starting clenaing process')

	df = _read_data(filename)
	newspaper_uid = _extract_newspaper_uid(filename)
	df = _add_newspaper_uid_column(df, newspaper_uid)
	df = _extract_host(df)
	df = _fill_missing_titles(df)
	df = _generate_uids_for_rows(df)
	df = _remove_new_lines_from_body(df)

	df['n_tokens_title'] = _tokenize_column(df , 'title') 
	df['n_tokens_body'] = _tokenize_column(df, 'body')

	df = _drop_rows_with_missing_values(df, 'body')
	df = _remove_duplicate_entries(df, 'title')


	_save_data(df, filename)



	return df



def _extract_host(df):
	logger.info('Extracting host from urls')
	df['host'] = df['url'].apply(lambda url: urlparse(url).netloc)

	return df


def _read_data(filename):
	logger.info('reading file {}'.format(filename))

	return pd.read_csv(filename)
	


def _extract_newspaper_uid(filename):
	logger.info('Extrac newspaper uid')
	newspaper_uid = filename.split('_')[0]

	logger.info('newspaper uid detected: {}'.format(newspaper_uid))
	return newspaper_uid


def _add_newspaper_uid_column(df, newspaper_uid):
	logger.info('Filling newspaper_uid column with {}'.format(newspaper_uid))
	df['newspaper_uid'] = newspaper_uid

	return df


def _fill_missing_titles(df):
	logger.info('filling missing titles')
	missing_titles_mask = df['title'].isna()

	missing_titles = (df[missing_titles_mask]['url']
		.str.extract(r'(?P<missing_titles>[^/]+)$')
		.applymap(lambda title: str(title).split('-'))
		.applymap(lambda title_word_list: ' '.join(title_word_list))
		)

	df.loc[missing_titles_mask, 'title'] = missing_titles.loc[:, 'missing_titles']

	print(missing_titles)

	return df

def _generate_uids_for_rows(df):
	logger.info('generating: uids for each row')
	uids = (df
		.apply( lambda row: hashlib.md5(bytes(row['url'].encode())), axis = 1)
		.apply(lambda hash_object: hash_object.hexdigest())
		)

	df['uid'] = uids

	return df.set_index('uid')


def _remove_new_lines_from_body(df):
	logger.info('remove new lines from body')

	stripped_body = (df
		.apply(lambda row: row['body'], axis = 1)
		.apply(lambda body: list(str(body)))
		.apply(lambda letters: list(map(lambda letter: letter.replace('\n',''), letters)))
		.apply(lambda letters: ''.join(letters))

		)
	df['body'] =  stripped_body

	return df

def _tokenize_column(df, column_name):
	logger.info('tokenizing data')

	stop_words = set(stopwords.words('spanish'))

	return (df
		.dropna()
		.apply(lambda row: nltk.word_tokenize(row[column_name]), axis = 1)
		.apply(lambda tokens: list(filter(lambda token: token.isalpha(), tokens)))
		.apply(lambda tokens: list(map(lambda token: str(token.lower()), tokens)))
		.apply(lambda word_list: list(filter(lambda word: word not in stop_words, word_list)))
		.apply(lambda valid_word_list: len(valid_word_list))
		)

def _remove_duplicate_entries(df, column_name):
	logger.info('Removing duplicate entries and nan values')

	
	df.drop_duplicates(subset=[column_name], keep='first', inplace=True)

	return df

def _drop_rows_with_missing_values(df, column_name):
	logger.info('Dropping rows with missing values')
	df=df[df[column_name]!='nan']
	df.dropna
	return df

def _save_data(df, filename):
	clean_filename = 'clean_{}'.format(filename) 
	logger.info('Saving data to location: {}'.format(clean_filename))
	df.to_csv(clean_filename)



if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument('filename',help='The path to the dirty data', type= str)
	args = parser.parse_args()

	df = main(args.filename)
	print(df)