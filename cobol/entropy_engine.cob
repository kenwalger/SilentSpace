      * ============================================================
      * SilentSpace Guardian -- Entropy Engine v1.0
      * Deterministic waste scoring for corporate meetings.
      *
      * Reads 6 scoring parameters from stdin, one per line:
      *   1. duration_minutes  (integer)
      *   2. attendee_count    (integer)
      *   3. has_agenda        (0 or 1)
      *   4. has_action_items  (0 or 1)
      *   5. could_be_email    (0 or 1)
      *   6. recurrence_level  (0=none 1=monthly 2=biweekly
      *                         3=weekly 4=daily)
      *
      * Output (two lines on stdout):
      *   Line 1: waste_score       (0-100)
      *   Line 2: necessity_prob    (5-100)
      *
      * Compile: cobc -x -o entropy_engine entropy_engine.cob
      * ============================================================
       IDENTIFICATION DIVISION.
       PROGRAM-ID. ENTROPY-ENGINE.

       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01 WS-DURATION           PIC 9(4)  VALUE ZEROS.
       01 WS-ATTENDEES          PIC 9(3)  VALUE ZEROS.
       01 WS-HAS-AGENDA         PIC 9(1)  VALUE ZEROS.
       01 WS-HAS-ACTIONS        PIC 9(1)  VALUE ZEROS.
       01 WS-COULD-BE-EMAIL     PIC 9(1)  VALUE ZEROS.
       01 WS-RECURRENCE         PIC 9(1)  VALUE ZEROS.

       01 WS-WASTE-SCORE        PIC 9(3)  VALUE ZEROS.
       01 WS-NECESSITY-PROB     PIC 9(3)  VALUE ZEROS.
       01 WS-TEMP               PIC 9(4)  VALUE ZEROS.

       PROCEDURE DIVISION.
       MAIN-LOGIC.
           ACCEPT WS-DURATION
           ACCEPT WS-ATTENDEES
           ACCEPT WS-HAS-AGENDA
           ACCEPT WS-HAS-ACTIONS
           ACCEPT WS-COULD-BE-EMAIL
           ACCEPT WS-RECURRENCE
           PERFORM COMPUTE-WASTE
           PERFORM COMPUTE-NECESSITY
           PERFORM DISPLAY-RESULTS
           STOP RUN.

       COMPUTE-WASTE.
      *    Base organizational entropy. Every meeting starts here.
           MOVE 20 TO WS-WASTE-SCORE

      *    Attendee bloat: 2 points per head above 3, capped at 30.
           IF WS-ATTENDEES > 3
               COMPUTE WS-TEMP = (WS-ATTENDEES - 3) * 2
               IF WS-TEMP > 30
                   MOVE 30 TO WS-TEMP
               END-IF
               ADD WS-TEMP TO WS-WASTE-SCORE
           END-IF

      *    Duration drag: 3 points per 15 minutes over 30.
           IF WS-DURATION > 30
               COMPUTE WS-TEMP = ((WS-DURATION - 30) / 15) * 3
               ADD WS-TEMP TO WS-WASTE-SCORE
           END-IF

      *    Recurrence tax: daily meetings are expensive.
           COMPUTE WS-TEMP = WS-RECURRENCE * 5
           ADD WS-TEMP TO WS-WASTE-SCORE

      *    Agendaless chaos premium.
           IF WS-HAS-AGENDA = 0
               ADD 15 TO WS-WASTE-SCORE
           END-IF

      *    Actionless void surcharge.
           IF WS-HAS-ACTIONS = 0
               ADD 10 TO WS-WASTE-SCORE
           END-IF

      *    Email crime penalty.
           IF WS-COULD-BE-EMAIL = 1
               ADD 20 TO WS-WASTE-SCORE
           END-IF

      *    Entropy is bounded. Unfortunately, so is the score.
           IF WS-WASTE-SCORE > 100
               MOVE 100 TO WS-WASTE-SCORE
           END-IF.

       COMPUTE-NECESSITY.
           COMPUTE WS-NECESSITY-PROB = 100 - WS-WASTE-SCORE
           IF WS-NECESSITY-PROB < 5
               MOVE 5 TO WS-NECESSITY-PROB
           END-IF.

       DISPLAY-RESULTS.
           DISPLAY WS-WASTE-SCORE
           DISPLAY WS-NECESSITY-PROB.
