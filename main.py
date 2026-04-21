from flask import Flask , render_template ,request , redirect , url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase , Mapped , mapped_column , relationship
from sqlalchemy import Integer ,String , Date , LargeBinary
from datetime import date
from sqlalchemy import desc   # ✅ import 
from sqlalchemy import Text, ForeignKey #🤖 AI work
import json                   #🤖 AI work 
import numpy as np
import datetime
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from ai_matcher import (
    generate_text_embedding,
    generate_image_embedding,
    final_similarity
)  #🤖 AI work

from dotenv import load_dotenv
load_dotenv()
# --------------------------------------------------------------------------------------------------------------------------------
# from co-pilot
import os 
from werkzeug.utils import secure_filename
# --------------------------------------------------------------------------------------------------------------------------------
#Cloudinary forthe image handling 

import cloudinary
import cloudinary.uploader

cloudinary.config(
    cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key = os.getenv("CLOUDINARY_API_KEY"),
    api_secret = os.getenv("CLOUDINARY_API_SECRET")
)

# --------------------------------------------------------------------------------------------------------------------------------

# intializing the simple  flask app
app = Flask(__name__)

# Uploadfolder from co-pilot
UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# -------------------------------------------------------------------------------------------------------------------------------
# Make sure the folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
# --------------------------------------------------------------------------------------------------------------------------------



# database class
class Base(DeclarativeBase):
    pass

# app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///lost_and_found.db"
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DB_URI", "sqlite:///lost_and_found.db")
db = SQLAlchemy(model_class=Base) #creating the db  using the class SQlALchemy 
db.init_app(app) 

# now creating the LostItem table just like how we used to create the class
class lostItem(db.Model):
    __tablename__ = "lost_item"
    id: Mapped[int] = mapped_column(Integer , primary_key=True)
    status:Mapped[str] = mapped_column(String , default="active")
    owner_Name: Mapped[str] = mapped_column(String , nullable=False)
    rollno: Mapped[str] = mapped_column(String ,  nullable=True) 
    itemName: Mapped[str] = mapped_column(String , nullable=False)
    category: Mapped[str] = mapped_column(String , nullable=False)
    location: Mapped[str] = mapped_column(String , nullable=False) 
    date: Mapped[Date]  = mapped_column(Date , nullable=False)
    description: Mapped[str] = mapped_column(String ,nullable=False)
    contact: Mapped[int] = mapped_column(Integer , nullable=False)
    email:Mapped[str] = mapped_column(String , nullable=False)
    filename: Mapped[str] = mapped_column(String,  nullable=True)
    # data: Mapped[LargeBinary] = mapped_column(LargeBinary)   
    owner_uniqueKey:Mapped[int] = mapped_column(Integer , nullable=False , unique=True)
    text_embedding = db.Column(db.Text)
    image_embedding = db.Column(db.Text)

# now creating the LostItem table just like how we used to create the class
class findItem(db.Model):
    __tablename__ = "find_item"
    findItem_id: Mapped[int] = mapped_column(Integer , primary_key=True)  
    status:Mapped[str] = mapped_column(String , default="active")
    fider_Name:Mapped[str] = mapped_column(String,nullable=False )
    find_item:Mapped[str] = mapped_column(String , nullable=False)
    findItem_category:Mapped[str] = mapped_column(String , nullable=False)
    findLocation:Mapped[str] = mapped_column(String , nullable=False)
    date_Find:Mapped[Date] =mapped_column(Date , nullable=False)
    findItem_Desc:Mapped[str] = mapped_column(String , nullable=False)
    finder_contact:Mapped[int] = mapped_column(Integer , nullable=False)
    finder_email:Mapped[str] = mapped_column(String , nullable=False) 
    findImg_filename: Mapped[str] = mapped_column(String , nullable=True)
    finder_uniqueKey:Mapped[int] = mapped_column(Integer , nullable=False , unique=True)
    text_embedding = db.Column(db.Text)
    image_embedding = db.Column(db.Text)

#now creating the match model 
class Match(db.Model):
    id: Mapped[int] = mapped_column(Integer , primary_key=True)
    lost_id: Mapped[int] = mapped_column(ForeignKey("lost_item.id"))
    found_id:Mapped[int] = mapped_column(ForeignKey("find_item.findItem_id"))
    similarity_score:Mapped[float] = mapped_column(nullable=False)
  
    status: Mapped[str] = mapped_column(String, default="pending")
    owner_confirmed:Mapped[bool] = mapped_column(default=False)
    finder_confirmed:Mapped[bool] = mapped_column(default=False)

    lost =  relationship("lostItem")
    found = relationship("findItem")


# finally creating the table 
with app.app_context():
    db.create_all()

#--------------------------------------------------------------------#-----------------------------------------------------------
# home router 
@app.route("/")
def home():
    # loading  data of the lostitem 
    with app.app_context():
        lost_data = db.session.execute(db.select(lostItem).where(lostItem.status == "active").order_by(desc(lostItem.date)))
        all_lostitem = lost_data.scalars().all()    # returns a list of LostItem objects
      #                                           .scalar() returns only the first row’s first column (or None if no rows exist).

        all_foundItem = db.session.execute(db.select(findItem).where(findItem.status=="active").order_by(desc(findItem. date_Find))).scalars().all() 
        noOf_matches = db.session.execute(db.select(Match)).scalars().all()
        
    return render_template("index.html" , lostData = all_lostitem , foundData = all_foundItem , no_of_AIdetection = 100 + len(noOf_matches)) 


#--------------------------------------------------------------------#-----------------------------------------------------------
# 
#lost items router : list of lost item 
@app.route("/lostItems")
def lost():
#   loading all data of lost items in the db  
    Lostitems_List = db.session.execute(db.select(lostItem).where(lostItem.status=="active").order_by(desc(lostItem.date))).scalars().all()   
     
# now just sending the data  
    return render_template("lost_items.html" , data = Lostitems_List)

#-----------------------------------------------------------------#---------------------------------------------------------------
# creating  the email  method 

def send_Ownermail(owners_mail , owner_name ,
                    lost_itemName , lost_itemLocation ,ai_score , finderName , found_location , finder_contact , finder_Email, ownerKey
                   ):
    senders_Mail = os.getenv("EMAIL_USER")
    receivers_mail = owners_mail 
    app_password = os.getenv("EMAIL_PASS")


    subject = "🎉 Possible Match Found for Your Lost Item!"  
    body = f""" 
            Hello {owner_name} , 

            Good news! 🎉

            We found a possible match for your lost item: 

            📝 Lost Item: {lost_itemName}
            📍 Lost Location: {lost_itemLocation}

            Match Confidence: {round(ai_score * 100, 2)}%

            Finder Details:
                👤 Name: {finderName}
                📍 Found Location: {found_location}
                📞 Contact: {finder_contact}
                📧 Email: {finder_Email}

            Please contact the finder to verify and collect your 
                   item.

            Note: If you received your Lost Item then kindly click on the 'owner confirm' button in the 'Item Matches' section to avoid reminder emails in future.
            
            Your Unique key: {ownerKey} 

            Regards,
            Lost & Found Portal  """
            
    msg = MIMEMultipart()
    msg["From"] =  senders_Mail
    msg["To"] = receivers_mail
    msg["Subject"] = subject

    msg.attach(MIMEText(body, "plain"))

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(senders_Mail, app_password)
        server.sendmail(senders_Mail, receivers_mail, msg.as_string())
        server.quit()

        print("📧 Email sent successfully!")

    except Exception as e:
        print("❌ Email sending failed:", e)
        return  redirect("/")

# sending the mail to the finder 
def send_finderMail(finder_mail, finder_name, found_itemName, found_location , ai_score ,owner_name , owner_contact, owner_mail , finderKey):
    senders_mail = os.getenv('EMAIL_USER')
    app_password = os.getenv('EMAIL_PASS')
    receivers_mail =  finder_mail
     
    subject = "🎉 Someone May Be the Owner of the Item You Found!" 
    body = f"""
     Hello {finder_name},

    Good news! 🎉

    Someone who reported a lost item may be the owner of the item you found:

    📝 Found Item: {found_itemName}
    📍 Found Location: {found_location}

    Match Confidence: {round(ai_score * 100, 2)}%

    Possible Owner Details:
    👤 Name: {owner_name}
    📞 Contact: {owner_contact}
    📧 Email: {owner_mail}

    Please contact them to verify ownership.
    
    Note: If you returned Lost Item then kindly click on the 'owner confirm' button in the 'Item Matches' section to avoid reminder emails in future.
   
     Your Unique key:{finderKey}
    
    Thank you for helping!
    Lost & Found Portal
    """

    msg = MIMEMultipart()
    msg['From'] = senders_mail
    msg['To'] =  receivers_mail
    msg['Subject'] = subject
        
    msg.attach(MIMEText(body,"plain"))

    try:
        connection = smtplib.SMTP("smtp.gmail.com",587)
        connection.starttls()   
        connection.login(senders_mail, password=app_password)
        connection.sendmail(senders_mail , receivers_mail , msg=msg.as_string())  
        connection.quit()

    except Exception as e:
        print("❌ Email sending failed:", e)
        return redirect("/") 
#--------------------------------------------------------------------#---------------------------------------------------------------
# creating the unique key generator function and returing the code
def uniqueKey_genrator():
    unique_code =  random.randint(1000,9999)
    return unique_code

def uniqueKey_checkerLost():
    while True:
        unique_key = uniqueKey_genrator()
        # all lost items
        lost_items = db.session.execute(db.select(lostItem)).scalars().all()
        # check if key exists in any item
        if all(lost_item.owner_uniqueKey != unique_key for lost_item in lost_items):
            return unique_key


def uniqueKey_checkerFound():
    while True:
        unique_Key = uniqueKey_genrator()
        found_items = db.session.execute(db.select(findItem)).scalars().all()
        # check if key exist lin any item
        if all(found_item.finder_uniqueKey != unique_Key for found_item in found_items):
            return unique_Key  
#--------------------------------------------------------------------#---------------------------------------------------------------
#found-items: list of found items 
@app.route("/foundItems")
def found():
    # fetching the all the founditems  data from the database and transfering them to the html file
    all_foundData = db.session.execute(db.select(findItem).where(findItem.status == "active").order_by(desc(findItem.date_Find))).scalars().all()
    
    return render_template("found_items.html" , found_data = all_foundData)


#--------------------------------------------------------------------#-----------------------------------------------------------
#reportlost items
@app.route("/report-LostItem", methods=['GET', 'POST'])
def report_lost():
    if request.method == 'POST':
        image = request.files['image']

        if image:
            # Upload to Cloudinary
            upload_result = cloudinary.uploader.upload(image)
            image_url = upload_result['secure_url']

            # Generate embeddings
            text_emb = generate_text_embedding(
                request.form['description'],
                request.form['location']
            )
            image_emb = generate_image_embedding(image_url)

            # Save URL in DB instead of filename
            new_data = lostItem(
                rollno=request.form['user_id'],
                owner_Name=request.form['user_Name'],
                itemName=request.form['title'],
                category=request.form['category'],
                location=request.form['location'],
                date=date.fromisoformat(request.form['date_lost']),
                contact=int(request.form['contactNo']),
                owner_uniqueKey=uniqueKey_checkerLost(),
                email=request.form["Email_id"],
                description=request.form['description'],
                filename=image_url,  # store Cloudinary URL
                text_embedding=json.dumps(text_emb),
                image_embedding=json.dumps(image_emb)
            )
            db.session.add(new_data)
            db.session.commit()

            return redirect(url_for("home"))

    return render_template("report_lost.html")

#---------------------------------------------------------------#-----------------------------------------------------------------
# report found item 
@app.route('/report-FoundItem', methods=['GET', 'POST'])
def report_found():
    if request.method == 'POST':
        found_img = request.files['fimage']
        if found_img:
            # Upload to Cloudinary
            upload_result = cloudinary.uploader.upload(found_img)
            image_url = upload_result['secure_url']

            # Save URL in DB
            newfound_Item = findItem(
                find_item=request.form['title'],
                fider_Name=request.form['finder_Name'],
                findItem_category=request.form['category'],
                findLocation=request.form['location_found'],
                date_Find=date.fromisoformat(request.form['date_found']),
                findItem_Desc=request.form['description'],
                finder_contact=request.form['contactNo'],
                finder_email=request.form['Email_id'],
                finder_uniqueKey=uniqueKey_checkerFound(),
                findImg_filename=image_url  # store Cloudinary URL
            )
            db.session.add(newfound_Item)
            db.session.commit()

            # Generate embeddings
            found_text_emb = generate_text_embedding(
                request.form['description'],
                request.form['location_found']
            )
            found_img_emb = generate_image_embedding(image_url)

            newfound_Item.text_embedding = json.dumps(found_text_emb)
            newfound_Item.image_embedding = json.dumps(found_img_emb)
            db.session.commit()
            
            # ===============================
            # 🤖 AI MATCHING STARTS HERE
            # ===============================

            # Fetch all lost items
            all_lost_items = db.session.execute(db.select(lostItem)).scalars().all()

            for lost in all_lost_items:
               if lost.text_embedding and lost.image_embedding:

                 lost_text_emb = np.array(json.loads(lost.text_embedding))
                 lost_img_emb = np.array(json.loads(lost.image_embedding))

                 score = final_similarity(
                   lost_text_emb,
                   found_text_emb,
                   lost_img_emb,
                   found_img_emb)

                 if score >= 0.78:
                    print(f"🔥 MATCH FOUND | Lost ID {lost.id} | Score: {score}")

                    existing_match = db.session.execute(db.select(Match).where(Match.lost_id == lost.id, Match.found_id == newfound_Item.findItem_id)).scalar()
 
                    if not existing_match:
                        new_match = Match(
                            lost_id=lost.id,
                            found_id=newfound_Item.findItem_id,
                            similarity_score=score)
                                  
                        db.session.add(new_match)
                        db.session.commit()
                    
                    # if match found sending the email by calling the function 
                        send_Ownermail(owners_mail=lost.email,owner_name=lost.owner_Name,lost_itemName=lost.itemName , lost_itemLocation= lost.location , ai_score=score , 
                                   finderName= newfound_Item.fider_Name , found_location= newfound_Item.findLocation, finder_contact=newfound_Item.finder_contact, 
                                   finder_Email=newfound_Item.finder_email, ownerKey= lost.owner_uniqueKey
                                   )
                        send_finderMail(finder_mail=newfound_Item.finder_email , finder_name=newfound_Item.fider_Name,
                                        found_itemName=newfound_Item.find_item , found_location=newfound_Item.findLocation,
                                        ai_score=score, owner_name= lost.owner_Name, owner_contact=lost.contact , owner_mail= lost.email, finderKey= newfound_Item.finder_uniqueKey
                                         )
            # ===============================
            # 🤖 AI MATCHING ENDS HERE
            # ===============================
             
            
            return redirect('/')

    return render_template('report_found.html')
    

#---------------------------------------------------------------#-----------------------------------------------------------------
# lost item show details  , by using the variable name
@app.route("/lostItem-details/<int:id>")
def lostItem_Details(id):
# grab the id and then load all the data using the  database 
 lost_item_id = id
#   now grabing all the details of that data using the database

 item_details = db.session.execute(db.select(lostItem).where(lostItem.id == lost_item_id)).scalar()
    #  now passing the item_details into the show_details template
 
 return render_template("show_details.html"  , viewDetails = item_details)     
#   note: scalar is used to  get the first row from the db , scalars() used to get the all the  data from the database  

#-----------------------------------------------------------------#---------------------------------------------------------------
# found item show details  , by using the variable name

# note TO-Do: for the showing the details for the lost and found item we are rendering the same html page/ template , which is 
@app.route("/founditem-details/<int:id>")
def foundItems_details(id):
    db_id = id
    #  now finding the details of that item from the database  
    found_ItemDetails = db.session.execute(db.select(findItem).where(findItem.findItem_id == db_id)).scalar()  
    
    #  now passing the item_details into the show_details template
    return render_template('show_details_found.html', details = found_ItemDetails )

#-----------------------------------------------------------------#---------------------------------------------------------------
# shows the all the matches object
@app.route('/matches')
def view_matches():
    matches = db.session.execute(
        db.select(Match)
    ).scalars().all()
    
    print("Hello")
   
    return render_template("matches.html", matches=matches)

#-----------------------------------------------------------------#---------------------------------------------------------------
# claim route
@app.route("/claim/<int:match_id>/<role>")
def claim(match_id , role):
    match = db.session.get(Match,match_id )#new thing explore

    if role =="owner":
       match.owner_confirmed = True

    if role == "finder":
        match.finder_confirmed = True

    if match.finder_confirmed and match.owner_confirmed:
        match.status = "completed"
        match.lost.status = "claimed" # able to access the   status of lostItem  tabel  because of the  relationship given in the match DB      
        match.found.status = "claimed"
    db.session.commit() 
    return redirect(url_for("view_matches"))      
#-----------------------------------------------------------------#---------------------------------------------------------------
# sending the reminder mail to the users  when the  match  status is pending after every alternativ days 
def send_reminderMail():
    senders_Mail = os.getenv("EMAIL_USER")
    app_Password = os.getenv("EMAIL_PASS")
    pending_status = db.session.execute(db.select(Match).where(Match.status == "pending")).scalars().all()
    for data in pending_status:
        Id_lost =  data.lost_id
        Id_found = data.found_id
        Score = data.similarity_score
        # fetching the each individual row using the id
        lost_details = db.session.execute(db.select(lostItem).where(lostItem.id ==Id_lost)).scalar() #using scalar because of the single item 
        found_details = db.session.execute(db.select(findItem).where(findItem.findItem_id==Id_found)).scalar()  #using scalar because of the single item
        if data.owner_confirmed == False:
            send_Ownermail(owners_mail=lost_details.email, owner_name=lost_details.owner_Name,
                            lost_itemName=lost_details.itemName, lost_itemLocation=lost_details.location,
                            ai_score= Score, finderName=found_details.fider_Name,
                            found_location=found_details.findLocation, finder_contact=found_details.finder_contact,
                            finder_Email=found_details.finder_email,  ownerKey= lost_details.owner_uniqueKey
                            )  
        if data.finder_confirmed== False:
            send_finderMail(finder_mail=found_details.finder_email , finder_name=found_details.fider_Name,
                            found_itemName=found_details.fider_Name , found_location=found_details.findLocation,
                            ai_score=Score, owner_name= lost_details.owner_Name, owner_contact=lost_details.contact , owner_mail= lost_details.email,
                            finderKey= found_details.finder_uniqueKey
                            )  


#--------------------------------------------------------------------#-----------------------------------------------------------
# calling the email reminder method by checking  using the if statement
today_datetime = datetime.datetime.now()
today_date = today_datetime.strftime("%d") #gives the date  in string format 

if int(today_date)% 2 == 0:                #if today date is  completely divided by 2 then we  call the method
    with app.app_context():
        send_reminderMail()



#-----------------------------------------------------------------#-----------------------------------------------------------------------------------------------   
@app.route("/submit_pin/<int:id>/<role>", methods=["GET", "POST"])
def submit_pin(id, role):
    matchId = id
    user_role = role

    if request.method == "POST":
        userPin = request.form['pin']
        match_result = db.session.execute(db.select(Match).where(Match.id == matchId)).scalar()

        if user_role == "owner":
            lost_results = db.session.execute(db.select(lostItem).where(lostItem.id == match_result.lost_id)).scalar()
            correctPin = lost_results.owner_uniqueKey
        else:  # finder
            found_results = db.session.execute(db.select(findItem).where(findItem.findItem_id == match_result.found_id)).scalar()
            correctPin = found_results.finder_uniqueKey

        if int(userPin) == correctPin:
            return redirect(url_for('claim', match_id=matchId, role=user_role))
        else:
            return render_template("pin_popUp.html", error=True, matcher_id=matchId, userRole=user_role)

    # GET request → show popup
    return render_template("pin_popUp.html", matcher_id=matchId, userRole=user_role)

#-----------------------------------------------------------------#-----------------------------------------------------------------------------------------------     
# about us 
@app.route("/about")
def about():
    return render_template("about.html")  


if __name__ == "__main__":
    app.run(debug=False)
