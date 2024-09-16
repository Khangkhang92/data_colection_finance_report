from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, ForeignKey
from sqlalchemy.orm import relationship
from .base import CommonModel

class PostGroup(CommonModel):
    __tablename__ = 'post_groups'

    post_group_id = Column(Integer, primary_key=True, autoincrement=True)
    fireant_post_group_id = Column(Integer, nullable=False, unique=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(String)

    posts = relationship("Post", back_populates="post_group")

    def __repr__(self):
        return f"<PostGroup(post_group_id={self.post_group_id}, name='{self.name}')>"

    @classmethod
    def from_json(cls, json_data):
        return {
            'fireant_post_group_id': json_data['postGroupID'],
            'name': json_data['name'],
            'description': json_data['description']
        }

class PostSource(CommonModel):
    __tablename__ = 'post_sources'

    post_source_id = Column(Integer, primary_key=True, autoincrement=True)
    fireant_post_source_id = Column(Integer, nullable=False, unique=True)
    name = Column(String, nullable=False, unique=True)
    url = Column(String)

    posts = relationship("Post", back_populates="post_source")

    def __repr__(self):
        return f"<PostSource(post_source_id={self.post_source_id}, name='{self.name}')>"

    @classmethod
    def from_json(cls, json_data):
        return {
            'fireant_post_source_id': json_data['postSourceID'],
            'name': json_data['name'],
            'url': json_data['url']
        }

class Post(CommonModel):
    __tablename__ = 'posts'

    post_id = Column(Integer, primary_key=True, autoincrement=True)
    fireant_post_id = Column(Integer, nullable=False, unique=True)
    post_group_id = Column(Integer, ForeignKey('post_groups.post_group_id'))
    post_source_id = Column(Integer, ForeignKey('post_sources.post_source_id'))
    date = Column(DateTime)
    title = Column(String)
    description = Column(String)
    is_source_content_full = Column(Boolean)
    post_source_url = Column(String, nullable=True)
    content = Column(String)
    original_content = Column(String)
    priority = Column(Integer)
    has_image = Column(Boolean)
    has_file = Column(Boolean)
    link = Column(String, nullable=True)
    link_image = Column(String, nullable=True)
    link_title = Column(String, nullable=True)
    link_description = Column(String, nullable=True)
    sentiment = Column(Float)
    approved = Column(Boolean)
    is_top = Column(Boolean)
    is_expert_idea = Column(Boolean)
    liked = Column(Boolean)
    total_likes = Column(Integer)
    total_replies = Column(Integer)
    total_shares = Column(Integer)

    post_group = relationship("PostGroup", back_populates="posts")
    post_source = relationship("PostSource", back_populates="posts")
    tagged_symbols = relationship("TaggedSymbol", back_populates="post")

    def __repr__(self):
        return f"<Post(post_id={self.post_id}, title='{self.title}')>"

    @classmethod
    def from_json(cls, json_data):
        post_data = {
            'fireant_post_id': json_data['postID'],
            'title': json_data['title'],
            'description': json_data['description'],
            'date': json_data['date'],
            'is_source_content_full': json_data['isSourceContentFull'],
            'post_source_url': json_data['postSourceUrl'],
            'content': json_data['content'],
            'original_content': json_data['originalContent'],
            'priority': json_data['priority'],
            'has_image': json_data['hasImage'],
            'has_file': json_data['hasFile'],
            'link': json_data['link'],
            'link_image': json_data['linkImage'],
            'link_title': json_data['linkTitle'],
            'link_description': json_data['linkDescription'],
            'sentiment': json_data['sentiment'],
            'approved': json_data['approved'],
            'is_top': json_data['isTop'],
            'is_expert_idea': json_data['isExpertIdea'],
            'liked': json_data['liked'],
            'total_likes': json_data['totalLikes'],
            'total_replies': json_data['totalReplies'],
            'total_shares': json_data['totalShares'],
        }
        return post_data

class TaggedSymbol(CommonModel):
    __tablename__ = 'tagged_symbols'

    id = Column(Integer, primary_key=True, autoincrement=True)
    post_id = Column(Integer, ForeignKey('posts.post_id'))
    symbol_ticker = Column(String(15), ForeignKey('symbol.ticker'))

    post = relationship("Post", back_populates="tagged_symbols")
    symbol = relationship("Symbol", back_populates="tagged_symbols")

    def __repr__(self):
        return f"<TaggedSymbol(id={self.id}, post_id={self.post_id}, symbol_ticker='{self.symbol_ticker}')>"
