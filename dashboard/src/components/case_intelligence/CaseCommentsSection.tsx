import React, { useState } from 'react';
import { MessageSquare, Send, Trash2, Edit2, Check, X } from 'lucide-react';
import { CaseComment } from '../../types';

interface CaseCommentsSectionProps {
  caseId: string;
  comments: CaseComment[];
  currentUserId?: string;
  isReadOnly?: boolean;
  onAddComment: (content: string) => Promise<void>;
  onEditComment: (commentId: string, content: string) => Promise<void>;
  onDeleteComment: (commentId: string) => Promise<void>;
}

export const CaseCommentsSection: React.FC<CaseCommentsSectionProps> = ({
  comments,
  isReadOnly = false,
  onAddComment,
  onEditComment,
  onDeleteComment,
}) => {
  const [newContent, setNewContent] = useState('');
  const [loading, setLoading] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editContent, setEditContent] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newContent.trim()) return;
    try {
      setLoading(true);
      await onAddComment(newContent);
      setNewContent('');
    } finally {
      setLoading(false);
    }
  };

  const startEdit = (c: CaseComment) => {
    setEditingId(c.comment_id);
    setEditContent(c.content);
  };

  const handleSaveEdit = async (commentId: string) => {
    if (!editContent.trim()) return;
    try {
      setLoading(true);
      await onEditComment(commentId, editContent);
      setEditingId(null);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 space-y-4">
      <div className="flex items-center gap-2 text-sm font-semibold text-slate-200">
        <MessageSquare className="h-4 w-4 text-cyan-400" />
        <span>Auditable Notes & Comments ({comments.length})</span>
      </div>

      {!isReadOnly && (
        <form onSubmit={handleSubmit} className="flex gap-2">
          <input
            type="text"
            value={newContent}
            onChange={(e) => setNewContent(e.target.value)}
            placeholder="Add investigation finding or hypothesis..."
            className="flex-1 bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-cyan-500"
          />
          <button
            type="submit"
            disabled={loading || !newContent.trim()}
            className="flex items-center gap-1 px-3 py-2 bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 text-white text-xs font-semibold rounded-lg transition-all"
          >
            <Send className="h-3.5 w-3.5" />
            <span>Post</span>
          </button>
        </form>
      )}

      <div className="space-y-3">
        {comments.map((c) => (
          <div key={c.comment_id} className="p-3 bg-slate-950 rounded-lg border border-slate-800/80 space-y-1.5 text-xs">
            <div className="flex items-center justify-between text-slate-400">
              <div className="flex items-center gap-2">
                <span className="font-semibold text-slate-200">{c.author_name}</span>
                <span className="text-[11px] text-slate-500">
                  {new Date(c.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </span>
                {c.is_edited && <span className="text-[10px] text-amber-400/80 italic">(edited)</span>}
              </div>
              {!isReadOnly && editingId !== c.comment_id && (
                <div className="flex items-center gap-1.5">
                  <button
                    onClick={() => startEdit(c)}
                    className="text-slate-500 hover:text-cyan-400 p-0.5 rounded"
                  >
                    <Edit2 className="h-3 w-3" />
                  </button>
                  <button
                    onClick={() => onDeleteComment(c.comment_id)}
                    className="text-slate-500 hover:text-rose-400 p-0.5 rounded"
                  >
                    <Trash2 className="h-3 w-3" />
                  </button>
                </div>
              )}
            </div>

            {editingId === c.comment_id ? (
              <div className="flex items-center gap-2 pt-1">
                <input
                  type="text"
                  value={editContent}
                  onChange={(e) => setEditContent(e.target.value)}
                  className="flex-1 bg-slate-900 border border-slate-700 rounded px-2 py-1 text-xs text-slate-200"
                />
                <button
                  onClick={() => handleSaveEdit(c.comment_id)}
                  className="text-emerald-400 p-1 hover:bg-emerald-500/10 rounded"
                >
                  <Check className="h-3.5 w-3.5" />
                </button>
                <button
                  onClick={() => setEditingId(null)}
                  className="text-slate-400 p-1 hover:bg-slate-700 rounded"
                >
                  <X className="h-3.5 w-3.5" />
                </button>
              </div>
            ) : (
              <p className="text-slate-300 leading-relaxed">{c.content}</p>
            )}
          </div>
        ))}
        {comments.length === 0 && (
          <div className="text-xs text-slate-500 italic">No notes or comments posted yet.</div>
        )}
      </div>
    </div>
  );
};
