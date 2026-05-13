import { useState, useEffect } from 'react';
import { createSession, listSessions } from '../api';

interface Session {
    id: number;
    name: string;
    created_at: string;
}

export default function SessionSelector({ onSelect }: { onSelect: (id: number) => void}) {
    const [sessions, setSessions] = useState<Session[]>([]);
    const [newName, setNewName] = useState("");

    useEffect(() => {
        listSessions().then(setSessions).catch(console.error);
    }, []);

    const handleCreate = async () => {
        if (!newName.trim()) return;
        const session = await createSession(newName);
        setSessions([...sessions, session]);
        setNewName("");
    };

    return (
        <div className='p-4 bg-white shadow rounded'>
            <h2 className='text-xl font-bold mb-2'>Sessions (Workspaces)</h2>
            <div className='flex gap-2 mb-4'>
                <input 
                    className='border px-2 py-1 rounded flex-1'
                    value={newName}
                    onChange={(e) => setNewName(e.target.value)}
                    placeholder="New session name"
                    onKeyDown={(e) => e.key === "Enter" && handleCreate()}
                />
                <button onClick={handleCreate} className='bg-blue-600 text-white px-3 py-1 rounded'>
                    Create
                </button>
            </div>
            <ul>
                {sessions.map((s) => (
                    <li key={s.id} className='py-1'>
                        <button onClick={() => onSelect(s.id)} className='text-blue-700 underline hover:no-underline'>
                            {s.name} (ID: {s.id})
                        </button>
                    </li>
                ))}
            </ul>
        </div>
    );
}