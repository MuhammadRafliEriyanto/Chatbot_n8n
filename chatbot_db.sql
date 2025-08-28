-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Aug 28, 2025 at 06:53 AM
-- Server version: 10.4.32-MariaDB
-- PHP Version: 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `chatbot_db`
--

-- --------------------------------------------------------

--
-- Table structure for table `admin`
--

CREATE TABLE `admin` (
  `id` int(11) NOT NULL,
  `name` varchar(120) NOT NULL,
  `email` varchar(120) NOT NULL,
  `password_hash` varchar(128) NOT NULL,
  `is_verified` tinyint(1) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `alembic_version`
--

CREATE TABLE `alembic_version` (
  `version_num` varchar(32) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `alembic_version`
--

INSERT INTO `alembic_version` (`version_num`) VALUES
('4173eeaf558f');

-- --------------------------------------------------------

--
-- Table structure for table `chat_history`
--

CREATE TABLE `chat_history` (
  `id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `session_id` varchar(100) NOT NULL,
  `message` text NOT NULL,
  `response` text DEFAULT NULL,
  `created_at` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `chat_history`
--

INSERT INTO `chat_history` (`id`, `user_id`, `session_id`, `message`, `response`, `created_at`) VALUES
(1, 2, 'fa44dad3-5705-4c67-ac00-27c418b28000', 'Halo chatbot!', 'No response', '2025-08-26 15:54:27'),
(2, 2, 'fa44dad3-5705-4c67-ac00-27c418b28000', 'Halo chatbot!', 'Webhook returned 404', '2025-08-26 15:56:34'),
(3, 2, '94ef24ef-6e1a-4f26-9b96-7a4f1cc9755b', 'Halo', 'Webhook returned 404', '2025-08-26 16:01:44'),
(4, 2, '3c77c6e2-1de8-4c46-9894-2e98256b4e7d', 'Halo chatbot!', 'Webhook returned 404', '2025-08-26 16:02:30'),
(5, 2, '72766d08-e46e-45a3-b58b-04d0c2074d1a', 'Halo chatbot!', 'Webhook returned 404', '2025-08-26 16:08:58'),
(6, 2, '92ff24c9-0b05-49e9-ba11-570f8b1a9edd', 'Halo chatbot!', 'Webhook returned 404', '2025-08-26 16:09:03'),
(7, 2, '662f4158-1fa7-411a-8031-2b54049403e6', 'Halo chatbot!', 'Halo, kak. Asalnya dari mana ya, kak?', '2025-08-26 16:19:23'),
(8, 2, '6243a93b-bc7a-4005-870a-f39c3ef279a1', 'Halo', 'Webhook returned 404', '2025-08-26 16:51:25'),
(9, 2, '3a676a41-2af9-4c51-aea6-13187731f624', 'Halo', 'Halo, kak. Ada yang bisa saya bantu terkait pelatihan, workshop, atau sertifikasi di Amikom Center? Silakan sampaikan pertanyaan kakak.', '2025-08-26 16:53:09');

-- --------------------------------------------------------

--
-- Table structure for table `user`
--

CREATE TABLE `user` (
  `id` int(11) NOT NULL,
  `name` varchar(120) NOT NULL,
  `email` varchar(120) NOT NULL,
  `password_hash` varchar(128) NOT NULL,
  `is_verified` tinyint(1) DEFAULT NULL,
  `phone_number` varchar(20) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `user`
--

INSERT INTO `user` (`id`, `name`, `email`, `password_hash`, `is_verified`, `phone_number`) VALUES
(2, 'Muhammad Rafli', 'raflieriyanto810@gmail.com', 'scrypt:QMLZMsbDNHJO80VTgr6S0Q==$MBTCOXvkhwAkCmzJ/0iUPobuD7bQxiXW5n3yIKQmE79yHppbBGw2hNrCXOMVQZ7++Jqk9barEgVj8GtpaaHi1g==', 1, '089618681090');

--
-- Indexes for dumped tables
--

--
-- Indexes for table `admin`
--
ALTER TABLE `admin`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `email` (`email`);

--
-- Indexes for table `alembic_version`
--
ALTER TABLE `alembic_version`
  ADD PRIMARY KEY (`version_num`);

--
-- Indexes for table `chat_history`
--
ALTER TABLE `chat_history`
  ADD PRIMARY KEY (`id`),
  ADD KEY `user_id` (`user_id`);

--
-- Indexes for table `user`
--
ALTER TABLE `user`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `email` (`email`),
  ADD UNIQUE KEY `phone_number` (`phone_number`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `admin`
--
ALTER TABLE `admin`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `chat_history`
--
ALTER TABLE `chat_history`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=10;

--
-- AUTO_INCREMENT for table `user`
--
ALTER TABLE `user`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `chat_history`
--
ALTER TABLE `chat_history`
  ADD CONSTRAINT `chat_history_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
