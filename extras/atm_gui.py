#ATM Machine


from flask import Flask, render_template_string, request, redirect, url_for
import webbrowser
import threading

app = Flask(__name__)

balance = 1000
correct_pin = "14"
logged_in = False
transactions = []

HTML_LOGIN = """
<!DOCTYPE html>
<html>
<head>
<title>ATM Login</title>

<style>

body{
font-family: Arial;
text-align:center;
background:#1f2a38;
color:white;
}

.keypad{
display:grid;
grid-template-columns:repeat(3,80px);
gap:10px;
justify-content:center;
}

button{
height:60px;
font-size:20px;
border:none;
background:#3498db;
color:white;
border-radius:8px;
}

.display{
width:200px;
height:40px;
font-size:20px;
text-align:center;
margin-bottom:20px;
}

</style>

<script>

function addNumber(num){
document.getElementById("pin").value += num;
}

function clearPin(){
document.getElementById("pin").value="";
}

</script>

</head>

<body>

<h2>ATM Login</h2>

<form method="POST">

<input type="password" id="pin" name="pin" class="display" readonly>

<div class="keypad">

<button type="button" onclick="addNumber(1)">1</button>
<button type="button" onclick="addNumber(2)">2</button>
<button type="button" onclick="addNumber(3)">3</button>

<button type="button" onclick="addNumber(4)">4</button>
<button type="button" onclick="addNumber(5)">5</button>
<button type="button" onclick="addNumber(6)">6</button>

<button type="button" onclick="addNumber(7)">7</button>
<button type="button" onclick="addNumber(8)">8</button>
<button type="button" onclick="addNumber(9)">9</button>

<button type="button" onclick="clearPin()">C</button>
<button type="button" onclick="addNumber(0)">0</button>
<button type="submit">Enter</button>

</div>

</form>

<h3>{{message}}</h3>

</body>
</html>
"""

HTML_MENU = """
<!DOCTYPE html>
<html>
<head>

<title>ATM Dashboard</title>

<style>

body{
font-family: Arial;
text-align:center;
background:#1f2a38;
color:white;
}

button{
height:60px;
width:80px;
font-size:20px;
border:none;
background:#3498db;
color:white;
border-radius:8px;
margin:5px;
}

input{
width:200px;
height:40px;
font-size:20px;
text-align:center;
margin-bottom:20px;
}

.keypad{
display:grid;
grid-template-columns:repeat(3,80px);
gap:10px;
justify-content:center;
margin-top:20px;
}

.action{
margin-top:20px;
}

.history{
margin-top:30px;
}

</style>

<script>

function addNumber(num){
document.getElementById("amount").value += num;
}

function clearAmount(){
document.getElementById("amount").value="";
}

</script>

</head>

<body>

<h2>ATM Dashboard</h2>

<h3>Current Balance: ₹ {{balance}}</h3>

<form method="POST">

<input type="text" id="amount" name="amount" placeholder="Enter Amount" readonly>

<div class="keypad">

<button type="button" onclick="addNumber(1)">1</button>
<button type="button" onclick="addNumber(2)">2</button>
<button type="button" onclick="addNumber(3)">3</button>

<button type="button" onclick="addNumber(4)">4</button>
<button type="button" onclick="addNumber(5)">5</button>
<button type="button" onclick="addNumber(6)">6</button>

<button type="button" onclick="addNumber(7)">7</button>
<button type="button" onclick="addNumber(8)">8</button>
<button type="button" onclick="addNumber(9)">9</button>

<button type="button" onclick="clearAmount()">C</button>
<button type="button" onclick="addNumber(0)">0</button>

</div>

<div class="action">

<button name="action" value="deposit">Deposit</button>
<button name="action" value="withdraw">Withdraw</button>

</div>

<br>

<a href="/logout">
<button type="button">Logout</button>
</a>


<div class="history">

<h3>Transaction History</h3>

<ul>

{% for t in transactions %}
<li>{{t}}</li>
{% endfor %}

</ul>

</div>

<h3>{{message}}</h3>

</body>
</html>
"""

@app.route("/", methods=["GET","POST"])
def home():

    message=""

    if request.method=="POST":

        pin=request.form["pin"]

        if pin==correct_pin:

            return """
            <script>
            window.location.href = "/dashboard";
            </script>
            """

        else:
            message="Wrong PIN"

    return render_template_string(HTML_LOGIN,message=message)

@app.route("/dashboard", methods=["GET","POST"])
def dashboard():

    global balance

    message=""

    if request.method=="POST":

        action = request.form.get("action")
        amount_str = request.form.get("amount","")

        if amount_str == "":
            message = "Please enter amount"
        else:

            try:
                amount = int(amount_str)

                if action == "deposit":

                    balance += amount
                    transactions.append(f"Deposited ₹{amount}")
                    message = "Deposit Successful"

                elif action == "withdraw":

                    if amount <= balance:

                        balance -= amount
                        transactions.append(f"Withdraw ₹{amount}")
                        message = "Withdrawal Successful"

                    else:
                        message = "Insufficient Balance"

            except:
                message = "Invalid Amount"

    return render_template_string(
        HTML_MENU,
        balance=balance,
        transactions=transactions,
        message=message
    )

@app.route("/logout",methods=["GET"])
def logout():

    global logged_in
    logged_in = False

    return redirect(url_for("home"))
def run():
    app.run(port=5000, debug=False, use_reloader=False)


threading.Thread(target=run).start()

webbrowser.open("http://127.0.0.1:5000")