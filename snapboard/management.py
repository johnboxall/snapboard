from django.dispatch import dispatcher 
from django.db.models import signals 

def sync_hook(): 
    # TODO
    pass

dispatcher.connect(sync_hook, signal=signals.post_syncdb) 




def test_setup():
    from django.contrib.auth.models import User
    from models import Thread, Post, Category
    from random import choice
    import chomsky

    # create 10 random users
    users = ('john', 'sally', 'susan', 'amanda', 'bob', 'tully', 'fran')
    for u in users:
        user = User.objects.get_or_create(username=u,
                password='foo')
        # user.is_staff = True

    cats = ('Random Topics',
            'Good Deals',
            'Skiing in the Vermont Area',
            'The Best Restaurants')
    for c in cats:
        cat = Category.objects.get_or_create(label=c)

    # create 50 threads
    tc = range(1, 50)
    for i in range(0, 100):
        cat= choice(Category.objects.all())
        subj = choice(chomsky.objects.split('\n'))
        thread = Thread(subject=subj, category=cat)
        thread.save()

        for j in range(0, choice(tc)):
            text = '\n\n'.join([chomsky.chomsky() for x in range(0, choice(range(2, 5)))])
            # create a post
            post = Post(
                    user=choice(User.objects.all()),
                    thread=thread,
                    text=text,
                    ip='.'.join([str(choice(range(1,255))) for x in (1,2,3,4)]),
                    )
            post.save()

