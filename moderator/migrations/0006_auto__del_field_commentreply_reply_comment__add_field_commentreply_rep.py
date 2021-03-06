# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'CommentReply.reply_comments'
        db.add_column('moderator_commentreply', 'reply_comments',
                      self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='reply_comments_set', null=True, to=orm['comments.Comment']),
                      keep_default=False)

        # Removing M2M table for field replied_to_comment on 'CommentReply'
        db.delete_table('moderator_commentreply_replied_to_comment')

        # Adding M2M table for field replied_to_comments on 'CommentReply'
        db.create_table('moderator_commentreply_replied_to_comments', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('commentreply', models.ForeignKey(orm['moderator.commentreply'], null=False)),
            ('comment', models.ForeignKey(orm['comments.comment'], null=False))
        ))
        db.create_unique('moderator_commentreply_replied_to_comments', ['commentreply_id', 'comment_id'])


    def backwards(self, orm):
        # Adding field 'CommentReply.reply_comment'
        db.add_column('moderator_commentreply', 'reply_comment',
                      self.gf('django.db.models.fields.related.ForeignKey')(related_name='reply_comment_set', null=True, to=orm['comments.Comment'], blank=True),
                      keep_default=False)

        # Deleting field 'CommentReply.reply_comments'
        db.delete_column('moderator_commentreply', 'reply_comments_id')

        # Adding M2M table for field replied_to_comment on 'CommentReply'
        db.create_table('moderator_commentreply_replied_to_comment', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('commentreply', models.ForeignKey(orm['moderator.commentreply'], null=False)),
            ('comment', models.ForeignKey(orm['comments.comment'], null=False))
        ))
        db.create_unique('moderator_commentreply_replied_to_comment', ['commentreply_id', 'comment_id'])

        # Removing M2M table for field replied_to_comments on 'CommentReply'
        db.delete_table('moderator_commentreply_replied_to_comments')


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'comments.comment': {
            'Meta': {'ordering': "('submit_date',)", 'object_name': 'Comment', 'db_table': "'django_comments'"},
            'comment': ('django.db.models.fields.TextField', [], {'max_length': '3000'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'content_type_set_for_comment'", 'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ip_address': ('django.db.models.fields.IPAddressField', [], {'max_length': '15', 'null': 'True', 'blank': 'True'}),
            'is_public': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_removed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'object_pk': ('django.db.models.fields.TextField', [], {}),
            'site': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['sites.Site']"}),
            'submit_date': ('django.db.models.fields.DateTimeField', [], {'default': 'None'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'comment_comments'", 'null': 'True', 'to': "orm['auth.User']"}),
            'user_email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'user_name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'user_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'moderator.cannedreply': {
            'Meta': {'object_name': 'CannedReply'},
            'comment': ('django.db.models.fields.TextField', [], {'max_length': '3000'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'site': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['sites.Site']", 'null': 'True', 'blank': 'True'})
        },
        'moderator.classifiedcomment': {
            'Meta': {'ordering': "['-comment__submit_date']", 'object_name': 'ClassifiedComment'},
            'cls': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'comment': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['comments.Comment']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'moderator.classifierstate': {
            'Meta': {'object_name': 'ClassifierState'},
            'ham_count': ('django.db.models.fields.IntegerField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'spam_count': ('django.db.models.fields.IntegerField', [], {})
        },
        'moderator.commentreply': {
            'Meta': {'object_name': 'CommentReply'},
            'canned_reply': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['moderator.CannedReply']", 'null': 'True', 'blank': 'True'}),
            'comment': ('django.db.models.fields.TextField', [], {'max_length': '3000', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'replied_to_comments': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'replied_to_comments_set'", 'symmetrical': 'False', 'to': "orm['comments.Comment']"}),
            'reply_comments': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'reply_comments_set'", 'null': 'True', 'to': "orm['comments.Comment']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'moderator.word': {
            'Meta': {'object_name': 'Word'},
            'ham_count': ('django.db.models.fields.IntegerField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'spam_count': ('django.db.models.fields.IntegerField', [], {}),
            'word': ('django.db.models.fields.CharField', [], {'max_length': '128'})
        },
        'secretballot.vote': {
            'Meta': {'unique_together': "(('token', 'content_type', 'object_id'),)", 'object_name': 'Vote'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'token': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'vote': ('django.db.models.fields.SmallIntegerField', [], {})
        },
        'sites.site': {
            'Meta': {'ordering': "('domain',)", 'object_name': 'Site', 'db_table': "'django_site'"},
            'domain': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        }
    }

    complete_apps = ['moderator']
