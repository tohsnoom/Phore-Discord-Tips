import discord, json, requests, pymysql.cursors
from cogs.utils import rpc
from discord.ext import commands

#result_set = database response with parameters from query
#db_bal = nomenclature for result_set["balance"]
#author = author from message context, identical to user in database
#wallet_bal = nomenclature for wallet reponse
class rpc:

	def listtransactions(params,count):
		port = "11311"
		rpc_user = 'srf2UUR0'
		rpc_pass = 'srf2UUR0XomxYkWw'
		serverURL = 'http://localhost:'+port
		headers = {'content-type': 'application/json'}

		payload = json.dumps({"method": "listtransactions", "params": [params,count], "jsonrpc": "2.0"})
		response = requests.get(serverURL, headers=headers, data=payload, auth=(rpc_user,rpc_pass))
		return(response.json()['result'])

class Balance:

	def __init__(self, bot):
		self.bot = bot

	def update_db(self, author, db_bal, lastblockhash):
		print("author => "+str(author))
		connection = pymysql.connect(host='localhost',
									user='root',
									password='',
									db='netcoin')
		cursor = connection.cursor(pymysql.cursors.DictCursor)
		try:
			cursor.execute("""
						UPDATE db
						SET balance=%s, lastblockhash=%s
						WHERE user
						LIKE %s
			""", (db_bal,lastblockhash,str(author)))
			connection.commit()
			print("Commited")
		except Exception as e:
			print("Error: "+str(e))
		return

	async def do_embed(self, author, db_bal):
		embed = discord.Embed(colour=discord.Colour.red())
		embed.add_field(name="User", value=author)
		embed.add_field(name="Balance (NET)", value="%.8f" % round(float(db_bal),8))
		embed.set_footer(text="Sponsored by altcointrain.com - Choo!!! Choo!!!")

		try:
			await self.bot.say(embed=embed)
		except discord.HTTPException:
			await self.bot.say("I need the `Embed links` permission to send this")
		return

	async def parse_part_bal(self,result_set,author):
		params = author
		count = 1000
		get_transactions = rpc.listtransactions(params,count)
		print(len(get_transactions))
		i = len(get_transactions)-1

		if len(get_transactions) == 0:
			print("0 transactions found for "+author+", balance must be 0")
			db_bal = 0
			await self.do_embed(author, db_bal)
		else:
			new_balance = float(result_set["balance"])
			lastblockhash = get_transactions[i]["blockhash"]
			print("LBH: ",lastblockhash)
			while i <= len(get_transactions):
				if get_transactions[i]["blockhash"] != result_set["lastblockhash"]:
					new_balance += float(get_transactions[i]["amount"])
					i -= 1
				else:
					new_balance += float(get_transactions[i]["amount"])
					print("New Balance: ",new_balance)
					break
			db_bal = float(new_balance)
			print("db_bal => "+str(db_bal))
			self.update_db(db_bal, author, lastblockhash)
			await self.do_embed(author, db_bal)

	async def parse_whole_bal(self,result_set,author):
		params = author
		count = 1000
		get_transactions = rpc.listtransactions(params,count)
		print(len(get_transactions))
		i = len(get_transactions)-1

		if len(get_transactions) == 0:
			print("0 transactions found for "+author+", balance must be 0")
			db_bal = 0
			await self.do_embed(author, db_bal)
		else:
			new_balance = 0
			lastblockhash = get_transactions[i]["blockhash"]
			firstblockhash = get_transactions[0]["blockhash"]
			print("FBH: ",firstblockhash)
			print("LBH: ",lastblockhash)
			while i <= len(get_transactions)-1:
				if get_transactions[i]["blockhash"] != firstblockhash:
					new_balance += float(get_transactions[i]["amount"])
					i -= 1
					print("New Balance: ",new_balance)
				else:
					new_balance += float(get_transactions[i]["amount"])
					print("New Balance: ",new_balance)
					break
			db_bal = new_balance
			self.update_db(db_bal,author,lastblockhash)
			await self.do_embed(author, db_bal)
			#Now update db with new balance

	@commands.command(pass_context=True)
	async def balance(self, ctx):
		#//Set important variables//
		author = str(ctx.message.author)

		#//Establish connection to db
		connection = pymysql.connect(host='localhost',
										user='root',
										password='',
										db='netcoin')
		cursor = connection.cursor(pymysql.cursors.DictCursor)

		#//Execute and return SQL Query
		try:
			cursor.execute("""SELECT balance, user, lastblockhash, tipped
							FROM db
							WHERE user
							LIKE %s
							""", str(author))
			result_set = cursor.fetchone()
			cursor.close()
		except Exception as e:
			print("Error in SQL query: ",str(e))
			return
		#//
		if result_set["lastblockhash"] == "0":
			await self.parse_whole_bal(result_set,author)
		else:
			await self.parse_part_bal(result_set,author)

def setup(bot):
	bot.add_cog(Balance(bot))
