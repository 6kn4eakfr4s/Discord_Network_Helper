import discord
import dns.exception
import requests
import json
from discord.ext import commands
import dns.resolver
from discord import app_commands
import speedtest
IPv4API= 'https://api.ipify.org'

config = open('config.json', 'r').read()
config_json = json.loads(config)
TOKEN = config_json['DiscordToken']


intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# dns query
def SpeedTest():
    s=speedtest.Speedtest()
    s.get_closest_servers()
    s.get_best_server()
    s.download()
    s.upload()
    s.results.share()
    result_url = list(s.results.dict()['share'])
    result_url.insert(4,'s')
    return ''.join(result_url)[0:-4]

def DNSQuery(domain, query_type):
    resolver = dns.resolver.Resolver()
    resolver.nameservers = ["8.8.8.8"]
    try:
        result_message = resolver.resolve(domain, query_type)
        result = result_message.rrset.to_text()
    except dns.resolver.NXDOMAIN:
        result = 'Non-existing domain!'
    except dns.resolver.NoAnswer:
        result = 'No records!'
    except dns.exception.Timeout:
        result = 'Time out!'
    except dns.resolver.LifetimeTimeout:
        result = 'Lifetime timeout!'
    except Exception as e:
        result = e
    return result

@tree.command(name= "current_ip", description= "print current public IP")
async def current_ip(ctx):
    currentIPv4 = requests.get(IPv4API).text
    await ctx.response.send_message('Current ipv4: ' + currentIPv4)

@tree.command(name= "speedtest", description="do a speedtest with speedtest-cli")
async def spdtest(ctx):
    await ctx.response.send_message("Testing")
    await ctx.edit_original_response(content= SpeedTest())

@tree.command(name= "dns_query", description="query a domain's DNS record")
async def dns_query(ctx, domain: str, query_type: str):
    result = DNSQuery(domain, query_type)
    await ctx.response.send_message(result)

@client.event
async def on_ready():
    await tree.sync()
    print("ready")
client.run(TOKEN)