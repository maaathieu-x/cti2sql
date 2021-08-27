

CREATE TABLE `events` (
  `id` int(11) NOT NULL,
  `QueueMemberSessionUUID` varchar(40) DEFAULT NULL,
  `Calling` varchar(14) DEFAULT NULL,
  `QueueMemberJoinedTime` datetime DEFAULT NULL,
  `QueueAgentAnsweredTime` datetime DEFAULT NULL,
  `Agent` varchar(14) DEFAULT NULL,
  `QueueMemberLeavingTime` datetime DEFAULT NULL,
  `QueueCause` varchar(20) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;


ALTER TABLE `events`
  ADD PRIMARY KEY (`id`);


ALTER TABLE `events`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;
COMMIT;


