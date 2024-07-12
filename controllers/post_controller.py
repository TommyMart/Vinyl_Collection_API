from datetime import datetime

from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from init import db
from controllers.comment_controller import comments_bp
from models.post import Post, post_schema, posts_schema


posts_bp = Blueprint("posts", __name__, url_prefix="/posts")
# Register the comments blueprint to the posts blueprint 
posts_bp.register_blueprint(comments_bp)

# /cards/ - GET - fetch all posts
@posts_bp.route("/")
def get_all_posts():
    # like SELECT * FROM posts and order in descending order
    # most recent first by date
    stmt = db.select(Post).order_by(Post.date.desc())
    posts = db.session.scalars(stmt)
    return posts_schema.dump(posts)

# /posts/<id> - GET - fetch a single post, using a dynamic route 
@posts_bp.route("/<int:post_id>")
def get_single_post(post_id):
    stmt = db.select(Post).filter_by(id=post_id)
    post = db.session.scalar(stmt)
    if post:
        return post_schema.dump(post)
    else:
        return {"error": f"Post with id {post_id} not found"}, 404
    
# /posts - POST a new post
@posts_bp.route("/", methods=["POST"])
# jwt_required decorator ensures a valid token is passed when creating 
# a new post
@jwt_required()
def new_post():
    # get the data from teh body of the request
    body_data = request.get_json()
    # create a new Post model instance
    # new post = Post model instance
    post = Post(
        title = body_data.get("title"),
        content = body_data.get("content"),
        date = datetime.now(),
        location = body_data.get("location"),
        image_url = body_data.get("image_url"),
        # get the user identity from the jwt token
        user_id = get_jwt_identity()
    )
    # add and commit to DB
    db.session.add(post)
    db.session.commit()
    # respond
    return post_schema.dump(post)

# /posts/<id> - DELETE a post, dynamic post_id
@posts_bp.route("/<int:post_id>", methods=["DELETE"])
@jwt_required()
def delete_post(post_id):
    # fetch the post from DB
    stmt = db.select(Post).filter_by(id=post_id)
    post = db.session.scalar(stmt)
    # if post exists
    if post:
        # delete the post
        db.session.delete(post)
        db.session.commit()
        return {"message": f"Post '{post.title}' deleted successfully"}

    # else 
    else:
        # return error message
        return {"error": f"Post with id {post_id} not found"}, 404
        
# /posts/<post_id> - PUT or PATCH, update a post
@posts_bp.route("/<int:post_id>", methods=["PUT", "PATCH"])
# user has to be logged in to update a post
@jwt_required()
def update_post(post_id):
    # fetch the data from the body of the request
    body_data = request.get_json()
    # get the card from the DB, post_id is id passed in route
    stmt = db.select(Post).filter_by(id=post_id)
    post = db.session.scalar(stmt)
    # if a card exists 
    if post:
        # update the fields as required
        # if the frontend has provided a title in payload,
        # update the title, if not, leave title as is
        post.title = body_data.get("title") or post.title
        post.content = body_data.get("content") or post.content
        post.date = body_data.get("date") or post.date
        post.location = body_data.get("location") or post.location
        post.image_url = body_data.get("image_url") or post.image_url
        # commit to the DB, don't need to add because already added to
        # session
        db.session.commit()
        # return response
        return post_schema.dump(post)
    #else
    else:
        # return an error 
        return {"error": f"Post with id {post_id} not found"}
    