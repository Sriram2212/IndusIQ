import React from 'react';
import { Settings2, AlertTriangle, CheckCircle, Clock, Activity, Gauge, Cpu } from 'lucide-react';

export const EquipmentCard = ({ equipment = null, entities = [] }) => {
  if (!equipment && (!entities || entities.length === 0)) {
    return null;
  }

  // If specific equipment telemetry is provided
  if (equipment) {
    return (
      <div className="two-column-grid animate-fade-in">
        {/* Equipment Specifications Card */}
        <div className="card-widget">
          <div className="card-widget-head">
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Settings2 size={16} style={{ color: 'var(--amber-primary)' }} />
              <h3 style={{ fontSize: '14px', textTransform: 'uppercase', color: '#ffffff' }}>
                Equipment Telemetry & Context
              </h3>
            </div>
            {equipment.tag && (
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--amber-primary)' }}>
                TAG: {equipment.tag}
              </span>
            )}
          </div>

          <div className="spec-key-value-grid">
            {equipment.model && (
              <div className="spec-item">
                <div className="spec-label">Equipment Model</div>
                <div className="spec-value">{equipment.model}</div>
              </div>
            )}
            {equipment.status && (
              <div className="spec-item">
                <div className="spec-label">Status</div>
                <div className="spec-value">{equipment.status}</div>
              </div>
            )}
            {equipment.vibration && (
              <div className="spec-item">
                <div className="spec-label">Vibration Status</div>
                <div className="spec-value" style={{ color: 'var(--amber-primary)' }}>
                  {equipment.vibration}
                </div>
              </div>
            )}
            {equipment.operatingHours && (
              <div className="spec-item">
                <div className="spec-label">Operating Hours</div>
                <div className="spec-value">{equipment.operatingHours}</div>
              </div>
            )}
          </div>
        </div>

        {/* Maintenance & Shift History Timeline if present */}
        {equipment.history && equipment.history.length > 0 && (
          <div className="card-widget">
            <div className="card-widget-head">
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Clock size={16} style={{ color: 'var(--cyan-primary)' }} />
                <h3 style={{ fontSize: '14px', textTransform: 'uppercase', color: '#ffffff' }}>
                  Maintenance Event Timeline
                </h3>
              </div>
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--text-muted)' }}>
                {equipment.history.length} EVENTS
              </span>
            </div>

            <div className="history-timeline">
              {equipment.history.map((event, idx) => (
                <div key={idx} className={`timeline-event ${event.flagged ? 'flagged' : ''}`}>
                  <span className="timeline-date">{event.date}</span>
                  <span className="timeline-text">{event.text}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  }

  // Display detected entities context card when entities are present
  return (
    <div className="card-widget animate-fade-in" style={{ marginTop: '16px' }}>
      <div className="card-widget-head">
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Cpu size={16} style={{ color: 'var(--cyan-primary)' }} />
          <h3 style={{ fontSize: '14px', textTransform: 'uppercase', color: '#ffffff' }}>
            Extracted Equipment & Entity Context
          </h3>
        </div>
        <span style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--text-muted)' }}>
          {entities.length} DETECTED
        </span>
      </div>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', padding: '8px 0' }}>
        {entities.map((ent, idx) => {
          const name = typeof ent === 'string' ? ent : (ent.name || ent.entity_id);
          const type = typeof ent === 'object' && ent.type ? ent.type : 'ENTITY';
          return (
            <span
              key={idx}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px',
                padding: '5px 10px',
                borderRadius: '4px',
                background: 'rgba(6, 182, 212, 0.1)',
                border: '1px solid rgba(6, 182, 212, 0.3)',
                color: '#e2e8f0',
                fontSize: '12px',
                fontFamily: 'var(--font-mono)'
              }}
            >
              <Activity size={12} style={{ color: 'var(--cyan-primary)' }} />
              <strong>{name}</strong>
              <span style={{ color: 'var(--text-muted)', fontSize: '10px' }}>[{type}]</span>
            </span>
          );
        })}
      </div>
    </div>
  );
};
