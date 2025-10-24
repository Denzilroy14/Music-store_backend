'''
                            Project:Music store
'''
#this is the main file for backend logic
#importing modules and libraries

from flask import*
import sqlite3
import os
from flask_cors import CORS
from werkzeug.security import generate_password_hash,check_password_hash

app=Flask(__name__)
CORS(app,supports_credentials=True,origins=['https://music-store-beige.vercel.app/'])

#database and configuration
app.config['SECRET_KEY']='ITS_ME_HERE@COOL-BUDDY'
app.config['UPLOADS']=os.path.join(app.root_path,'uploads')

def init_db():
    con=sqlite3.connect('database.db')
    cur=con.cursor()
    cur.execute('CREATE TABLE IF NOT EXISTS products(id INTEGER PRIMARY KEY AUTOINCREMENT,prod_name TEXT,prod_desc TEXT,prod_amt FLOAT,prod_count INTEGER,prod_img_name TEXT)')
    cur.execute('CREATE TABLE IF NOT EXISTS usercart(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER,prod_id INTEGER,prod_name TEXT,prod_amt FLOAT,prod_quan FLOAT,prod_img_name TEXT,foreign key(user_id)references user(id),foreign key(prod_id)references products(id))')
    cur.execute('CREATE TABLE IF NOT EXISTS user(id INTEGER PRIMARY KEY AUTOINCREMENT,username TEXT,password TEXT,email TEXT)')
    cur.execute('CREATE TABLE IF NOT EXISTS review(id INTEGER PRIMARY KEY AUTOINCREMENT,comment TEXT,rating INTEGER,prod_id INTEGER,user_name TEXT,foreign key(prod_id)references products(id))')
    con.commit()
init_db()
#home url
@app.route('/home',methods=['GET'])
def home():
    con=sqlite3.connect('database.db')
    curr=con.cursor()
    products=curr.execute('SELECT * FROM products').fetchall()

    product_list=[]
    for data in products:
        product_list.append({
            'product_id':data[0],
            'product_name':data[1],
            'product_desc':data[2],
            'product_amt':data[3],
            'product_qty':data[4],
            'product_img_url':f'http://localhost:5000/uploads/{data[5]}'
        })
    return jsonify(product_list)
#sigin url
@app.route('/signin',methods=['POST'])
def signin():
    username=request.form['username']
    email=request.form['email']
    password=request.form['password']
    confirm_password=request.form['confirm_password']
    if password==confirm_password:
        final_password=generate_password_hash(confirm_password,method='pbkdf2:sha256')
        con=sqlite3.connect('database.db')
        curr=con.cursor()
        curr.execute('INSERT INTO user(username,password,email)VALUES(?,?,?)',(username,final_password,email))
        con.commit()
        return jsonify({'message':'Successfully registered'})
    else:
        return jsonify({'message':'Password and confirm password do not match'})

#login url
@app.route('/login',methods=['POST'])
def login():
    username=request.form['username']
    password=request.form['password']
    if password and username:
        con=sqlite3.connect('database.db')
        cur=con.cursor()
        user=cur.execute('SELECT * FROM user WHERE username=?',(username,)).fetchone()
        user_password=user[2]
        if user and check_password_hash(user_password,password):
            session['user_id']=user[0]
            #return redirect(url_for('home'))  this will give a 302 error
            return jsonify({'message':'Login succesfull'}),200
        else:
            return jsonify({'message':'incorrect details!'}),401
    else:
        return jsonify({'message':'Please enter your password and username!'}),400
    
#profile url
@app.route('/profile',methods=['GET'])
def profile():
    if 'user_id' in session:
        user_id=session.get('user_id')
        con=sqlite3.connect('database.db')
        curr=con.cursor()
        # user=curr.execute('SELECT * FROM user WHERE id=?',(user_id,)).fetchone()
        cart_items=curr.execute('SELECT * FROM usercart WHERE user_id=?',(user_id,)).fetchall()
        user_name=curr.execute('SELECT id,username FROM user WHERE id=?',(user_id,)).fetchone()
        user_cart_items=[]
        for item in cart_items:
            user_cart_items.append({
                'user_id':user_name[0],
                'username':user_name[1],
                'product_id':item[2],
                'product_name':item[3],
                'product_amt':item[4],
                'product_qty':item[5],
                'product_img':f'http://localhost:5000/uploads/{item[6]}'
                })

        return jsonify(user_cart_items)
    else:
        #return redirect(url_for('login')) will give a 302 error in frontend
        return jsonify({'error':'Not logged in'}),401
#add to cart url
@app.route('/add_to_cart/<int:prodid>',methods=['POST'])
def add_to_cart(prodid):
    if 'user_id' not in session:
        return jsonify({'message':'please to add item'}),401
    #quan=request.form['quantity']request.form only works when the frontend sends the data using application/x-www-form-urlencoded or multipart/form-data — which is how regular HTML forms behave.
    # But in your React + Axios app, you're sending data as JSON, so Flask needs to parse it differently.
    else:
        user_id=session.get('user_id')
        data=request.get_json()#right way to get data from frontend when using react and axios
        quan=int(data.get('quantity',1))
        con=sqlite3.connect('database.db')
        cur=con.cursor()
        products=cur.execute('SELECT * FROM products WHERE id=?',(prodid,)).fetchone()
        cur.execute('INSERT INTO usercart(user_id,prod_id,prod_name,prod_amt,prod_quan,prod_img_name)VALUES(?,?,?,?,?,?)',(user_id,prodid,products[1],products[3],quan,products[5]))
        con.commit()
        return jsonify({'message':'product added successfully!'}),200

#feedback url
@app.route('/give_feedback',methods=['POST'])
def give_feedback():
    data=request.get_json()
    prod_id=data.get('prod_id')
    rating=data.get('rating')
    comment=data.get('comment')
    userid=session.get('user_id')
    con=sqlite3.connect('database.db')
    curr=con.cursor()
    username=curr.execute('SELECT username FROM user WHERE id=?',(userid,)).fetchone()
    curr.execute('INSERT INTO review(user_name,comment,prod_id,rating)VALUES(?,?,?,?)',(username,comment,prod_id,rating))
    con.commit()
    return jsonify({'message':'feedback submited successfully!'})
@app.route('/view_product_details/<int:prodid>',methods=['GET'])
def view_product_details(prodid):
    con=sqlite3.connect('database.db')
    curr=con.cursor()
    product=curr.execute('SELECT * FROM products WHERE id=?',(prodid,)).fetchone()
    reviews=curr.execute('''SELECT * FROM review WHERE prod_id=?''',(prodid,)).fetchall()
    '''reviews_list=[
        {'username':reviews[0],'review':reviews[1],'rating':reviews[2]}
    ]'''
    details_list={
        'product_name':product[1],
        'product_desc':product[2],
        'product_amt':product[3],
        'product_qty':product[4],
        'product_img_url':f'http://localhost:5000/uploads/{product[5]}',
        'reviews':reviews
        }
    return jsonify(details_list)
@app.route('/my_orders',methods=['GET'])
def my_orders():
    if 'user_id' not in session:
        return jsonify({"message":"Log in to your account!"}),401
    user_id=session['user_id']
    con=sqlite3.connect('database.db')
    cur=con.cursor()
    data=cur.execute('SELECT * FROM user_orders WHERE user_id=?',(user_id,)).fetchall()
    orders=[]
    for item in data:
        orders.append({                                                       
            'prod_id':item[2],
            'prod_name':item[3],
            'prod_amt':item[4],
            'Total_amt':item[5],
            'ordered_quan':item[7],
            'prod_img_name':f'http://localhost:5000/uploads/{item[8]}',
            'product_status':item[9]
            })
    if orders:
        return jsonify(orders)
    else:
        return jsonify({'message':'No orders found'}) 

#-----------------------------Admin panel-----------------------------------------------------
#url to add product
@app.route('/add_product',methods=['POST'])
def add_product():
    prod_name=request.form['prod_name']
    prod_amt=request.form['prod_amt']
    prod_qty=request.form['prod_qty']
    prod_desc=request.form['prod_desc']
    prod_img=request.files['prod_image']
    if prod_img:
        filename=prod_img.filename
        filepath=os.path.join(app.config['UPLOADS'],filename)
        prod_img.save(filepath)

        con=sqlite3.connect('database.db')
        cur=con.cursor()
        cur.execute('INSERT INTO products(prod_name,prod_desc,prod_amt,prod_count,prod_img_name)VALUES(?,?,?,?,?)',(prod_name,prod_desc,prod_amt,prod_qty,filename))
        con.commit()
        return jsonify({'message':'products added to list Succesfully!'})
#bill now
@app.route('/billnow/<int:prod_id>/<int:user_id>/<int:qty>',methods=['GET','POST'])
def billnow(prod_id,user_id,qty):
    con=sqlite3.connect('database.db')
    cur=con.cursor()
    shipping_data=request.get_json()
    contact=shipping_data.get('contact')
    address=shipping_data.get('address')
    payment_method=shipping_data.get('payment_method')
    username=cur.execute('SELECT username FROM user WHERE id=?',(user_id,)).fetchall()[0][0]
    product=cur.execute('SELECT * FROM products WHERE id=?',(prod_id,)).fetchone()
    if product:
        update_quan=product[4]-int(qty)
        cur.execute('UPDATE products SET prod_count=? WHERE id=?',(update_quan,prod_id,))
        con.commit()
        bill=product[3]*qty
        cur.execute('INSERT INTO shipping_details(user_id,user_name,user_contact,user_address_one,payment_mode,prod_quantity,prod_id,prod_name,prod_img_name,total_amt)VALUES(?,?,?,?,?,?,?,?,?,?)',(user_id,username,contact,address,payment_method,qty,prod_id,product[1],product[5],bill))
        cur.execute('INSERT INTO user_orders(user_id,prod_id,prod_name,prod_amt,prod_quan,prod_img_name,product_status,user_ordered_qty,total_price)VALUES(?,?,?,?,?,?,?,?,?)',(user_id,prod_id,product[1],product[3],product[4],product[5],False,qty,bill))
        con.commit()
        cur.execute('DELETE FROM usercart WHERE prod_id=? and user_id=?',(prod_id,user_id,))
        con.commit()
        return jsonify({'message':'bill complete!','bill':bill})
    else:
        return jsonify({'message':'product do not exists'})
'''
@app.route('/shipping',methods=['POST'])
def shipping():
    user_id=session.get('user_id')
    if not user_id:
        return jsonify({'message':'please log in to complete your order!'}),401
    shipping_data=request.get_json()
    prod_id=shipping_data.get('prod_id')
    contact=shipping_data.get('contact')
    address=shipping_data.get('address')
    total_bill=shipping_data.get('total_bill')
    prod_qty=shipping_data.get('prod_qty')
    payment_method=shipping_data.get('payment_method')
    con=sqlite3.connect('database.db')
    cur=con.cursor()
    products=cur.execute('SELECT * FROM products WHERE id=?',(prod_id,)).fetchone()
    username=cur.execute('SELECT username FROM user WHERE id=?',(user_id,)).fetchone()
    cur.execute('INSERT INTO shipping_details(user_id,user_name,user_contact,user_address_one,payment_mode,prod_quantity,prod_id,prod_name,prod_img_name,total_amt)VALUES(?,?,?,?,?,?,?,?,?,?)',(user_id,username,contact,address,payment_method,prod_qty,prod_id,products[1],products[5],total_bill))
    con.commit()
    return jsonify({'message':'Shipping successfully'})
''' 
@app.route('/view_products',methods=['GET'])
def view_product():
    con=sqlite3.connect('database.db')
    cur=con.cursor()
    products=cur.execute('SELECT * FROM products').fetchall()
    product_list=[]
    for data in products:
        product_list.append({
            'product_id':data[0],
            'product_name':data[1],
            'product_desc':data[2],
            'product_amt':data[3],
            'product_qty':data[4],
            'product_img_url':f'http://localhost:5000/uploads/{data[5]}'
        })
    return jsonify(product_list)
@app.route('/delete_products',methods=['POST'])
def delete_products():
    selected_id=request.form.getlist('product_to_delete')
    placeholder=','.join(['?']*len(selected_id))
    query=f'SELECT * FROM products WHERE id IN({placeholder})'
    con=sqlite3.connect('database.db')
    cur=con.cursor()
    selected_products=cur.execute(query,selected_id).fetchall()
    for item in selected_products:
        cur.execute('DELETE FROM products WHERE id=?',(item[0],))
        con.commit()
    return redirect(url_for('home')) 
@app.route('/manage_orders',methods=['GET'])
def manage_orders():
    con=sqlite3.connect('database.db')
    cur=con.cursor()
    received_orders=cur.execute('''SELECT * FROM user_orders
                                JOIN shipping_details ON user_orders.user_id=shipping_details.user_id
                                ''').fetchall()
    orders_list=[]
    for order in received_orders:
        orders_list.append({
            'user_id':order[1],
            'user_name':order[12],
            'usercontact':order[13],
            'user_address':order[14],
            'payment_option':order[15],
            'prod_id':order[2],
            'product_name':order[3],
            'Total_amount':order[5],
            'ordered_qty':order[7],
            'product_image_name':f'http://localhost:5000/uploads/{order[8]}',
            'product_status':order[9],
        })
    return jsonify(orders_list)
@app.route('/update_order_status',methods=['POST'])
def update_order_status():
    data=request.get_json()
    user_id=data.get('user_id')
    prod_id=data.get('prod_id')
    new_status=data.get('new_status')   
    con=sqlite3.connect('database.db')
    cur=con.cursor()
    cur.execute('UPDATE user_orders SET product_status=? WHERE user_id=? AND prod_id=?',(new_status,user_id,prod_id,))
    con.commit()
    return jsonify({'message':'Order status updated successfully!'})
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOADS'],filename)

#con=sqlite3.connect('database.db')
#curr=con.cursor()
#curr.execute('CREATE TABLE IF NOT EXISTS user_orders(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER,prod_id INTEGER,prod_name TEXT,prod_amt FLOAT,total_price FLOAT,prod_quan FLOAT,user_ordered_qty INTEGER,prod_img_name TEXT,product_status BOOLEAN,foreign key(user_id)references user(id),foreign key(prod_id)references products(id))')
#curr.execute('CREATE TABLE IF NOT EXISTS shipping_details(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER,user_name TEXT,user_contact TEXT,user_address_one TEXT,payment_mode TEXT,prod_quantity INTEGER,prod_id INTEGER,prod_name TEXT,prod_img_name TEXT,total_amt FLOAT,foreign key(user_id)references user(id),foreign key(prod_id)references products(id))')
#curr.execute('ALTER TABLE review ADD COLUMN userid INTEGER')
#data=curr.execute('SELECT * FROM user_orders').fetchall()
#data=curr.execute('SELECT * FROM products WHERE id=2').fetchone()
#curr.execute('DELETE FROM usercart WHERE user_id=1')
#curr.execute('DELETE FROM review')
#data=curr.execute('SELECT * FROM products').fetchall()
#print(data)
#curr.execute('DELETE FROM user_orders')
#con.commit()
#print("deleted")
#print("User cart delete")
#print("added column")
if __name__=='__main__':
    if not os.path.exists(app.config['UPLOADS']):
        os.mkdir(app.config['UPLOADS'])
    app.run(debug=True)









































































