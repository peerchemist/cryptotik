# cryptotik
Standardized common API for several cryptocurrency exchanges.

## Install

`pip install git+git://github.com/peerchemist/cryptotik.git`

## Examples

Right now library supports: Btce, Poloniex, Bittrex, TheRockTrading, HitBtc, Livecoin, OKcoin.

`from cryptotik import Btce, Bittrex, Poloniex, TheRock`

You only need to learn commands once, for example `get_markets` will work anywhere

`Bittrex.get_markets()`

`Poloniex.get_markets()`

`Btce.get_markets()`

`TheRock.get_markets()`

and will yield similar results. However parsing and interpreting them is left to user.

## More examples

`Btce.get_market_ticker("ppc-btc")`

`Poloniex.get_market_order_book("btc-nxt")`

`Bittrex.get_market_depth("btc-maid")`

## Private API methods (the ones that require authentication)

Library also supports private API methods for Poloniex and Bittrex, 
to use them you need to make class instance though with your API credentials.

`polo = Poloniex(yourkey, yoursecret)`

`polo.get_balances()`

`polo.withdraw(<coin>, <amount>, <address>)`

Same goes for Bittrex:

`btrx = Bittrex(yourkey, yoursecret)`

`btrx.get_balances()`

`btrx.withdraw(<coin>, <amount>, <address>)`

----------------------------------------------------------

<!DOCTYPE html>
<html>
<head>
<meta name="peercoin" content="PHbynAL8Pb4yBVTfhYi9Qa3L8m4JZJQqJ5">
<style>

    .text {
        
        color:#333333;
        font-family:arial;
        font-size:35px;
        font-weight:bold;
        
        text-decoration:none;
        
        text-shadow:0px 1px 0px #ffee66;
        
    }

    .myButton {
        
        -moz-box-shadow:inset 0px 1px 0px 0px #fff6af;
        -webkit-box-shadow:inset 0px 1px 0px 0px #fff6af;
        box-shadow:inset 0px 1px 0px 0px #fff6af;
        
        background:-webkit-gradient(linear, left top, left bottom, color-stop(0.05, #ffec64), color-stop(1, #3CB054));
        background:-moz-linear-gradient(top, #ffec64 5%, #3CB054 100%);
        background:-webkit-linear-gradient(top, #ffec64 5%, #3CB054 100%);
        background:-o-linear-gradient(top, #ffec64 5%, #3CB054 100%);
        background:-ms-linear-gradient(top, #ffec64 5%, #3CB054 100%);
        background:linear-gradient(to bottom, #ffec64 5%, #3CB054 100%);
        filter:progid:DXImageTransform.Microsoft.gradient(startColorstr='#ffec64', endColorstr='#3CB054',GradientType=0);
        
        background-color:#3CB054;
        
        -moz-border-radius:6px;
        -webkit-border-radius:6px;
        border-radius:6px;
        
        border:1px solid #373737;
        
        display:inline-block;
        color:#333333;
        font-family:arial;
        font-size:15px;
        font-weight:bold;
        padding:6px 24px;
        text-decoration:none;
        
        text-shadow:0px 1px 0px #ffee66;
        
    }
    .myButton:hover {
        
        background:-webkit-gradient(linear, left top, left bottom, color-stop(0.05, #3CB054), color-stop(1, #ffec64));
        background:-moz-linear-gradient(top, #3CB054 5%, #ffec64 100%);
        background:-webkit-linear-gradient(top, #3CB054 5%, #ffec64 100%);
        background:-o-linear-gradient(top, #3CB054 5%, #ffec64 100%);
        background:-ms-linear-gradient(top, #3CB054 5%, #ffec64 100%);
        background:linear-gradient(to bottom, #3CB054 5%, #ffec64 100%);
        filter:progid:DXImageTransform.Microsoft.gradient(startColorstr='#3CB054', endColorstr='#ffec64',GradientType=0);
        
        background-color:#3CB054;
    }
    .myButton:active {
        position:relative;
        top:1px;
    }

</style>
</head>
<body>

<p id="demo" class="text">Please consider supporting this project in Peercoin.</p>

<button onclick="myFunction()" class="myButton">Donate</button>

<script>
function getBitcoinAddr() { 
   var metas = document.getElementsByTagName('meta'); 

   for (i=0; i<metas.length; i++) { 
      if (metas[i].getAttribute("property") == "peercoin") { 
         return metas[i].getAttribute("content"); 
      } 
   } 

    return "";
} 
function myFunction()
{
var x;
var r=confirm;javascript:window.prompt ('Please send a donation to our Peercoin address:', getBitcoinAddr());
if (r==true)
  {
  x="Thank you!";
  }
else
  {
  x="Thank you!";
  }
document.getElementById("demo").innerHTML=x;
}
</script>

</body>
</html>