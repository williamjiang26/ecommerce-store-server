import strawberry



@strawberry.type
class Message:
    sender: str
    text: str

# get chat stream
# how does this work, when new conversation comes up, a conversation is added to the list
# add conversation
# delete conversation
# create a manual conversational chat between admin dashboard and website
# handle multiple conversations in the dashboard
# both clients send message to the server and poll the server for new message, the render the chats different based on user on their own end
