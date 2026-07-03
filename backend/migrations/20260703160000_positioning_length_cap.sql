-- Positioning is a short stance label ("megabull", or whatever the user types),
-- not a sentence. Cap it at 15 characters at the database level too.

alter table narratives
    add constraint narratives_positioning_len
    check (positioning is null or char_length(positioning) <= 15);
