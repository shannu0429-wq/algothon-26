create database if not exists `jobalign_ai` character set utf8mb4 collate utf8mb4_unicode_ci;
use `jobalign_ai`;

create table if not exists `ss_users` (
  `id` int not null auto_increment,
  `name` varchar(150) not null,
  `email` varchar(191) not null,
  `password_hash` varchar(255) not null,
  `location` varchar(150) default '',
  `linkedin` varchar(255) default '',
  `github` varchar(255) default '',
  `portfolio` varchar(255) default '',
  `career_interests` varchar(255) default '',
  `created_at` datetime not null,
  primary key (`id`),
  unique key `idx_ss_users_email` (`email`)
) engine=innodb default charset=utf8mb4 collate=utf8mb4_unicode_ci;

create table if not exists `ss_resumes` (
  `id` int not null auto_increment,
  `user_id` int not null,
  `filename` varchar(255) not null,
  `extracted_text` longtext not null,
  `parsed_data` longtext not null,
  `uploaded_at` datetime not null,
  primary key (`id`),
  key `idx_ss_resumes_user_id` (`user_id`),
  constraint `fk_ss_resumes_user` foreign key (`user_id`) references `ss_users` (`id`) on delete cascade
) engine=innodb default charset=utf8mb4 collate=utf8mb4_unicode_ci;

create table if not exists `ss_jobs` (
  `id` int not null auto_increment,
  `title` varchar(200) not null,
  `company` varchar(200) not null,
  `location` varchar(150) not null,
  `description` longtext not null,
  `required_skills` text not null,
  `preferred_skills` text not null,
  `experience_required` varchar(100) not null,
  `education_required` varchar(150) not null,
  `job_type` varchar(50) not null default 'full-time',
  `created_at` datetime not null,
  primary key (`id`),
  key `idx_ss_jobs_title` (`title`),
  key `idx_ss_jobs_company` (`company`),
  key `idx_ss_jobs_location` (`location`)
) engine=innodb default charset=utf8mb4 collate=utf8mb4_unicode_ci;

create table if not exists `ss_matches` (
  `id` int not null auto_increment,
  `user_id` int not null,
  `resume_id` int not null,
  `job_id` int default null,
  `job_title` varchar(200) default null,
  `company_name` varchar(200) default null,
  `overall_score` float not null default 0,
  `skill_score` float not null default 0,
  `experience_score` float not null default 0,
  `semantic_score` float not null default 0,
  `education_score` float not null default 0,
  `project_score` float not null default 0,
  `matched_skills` text not null,
  `missing_skills` text not null,
  `partial_skills` text not null,
  `explanation` text not null,
  `recommendations` text not null,
  `created_at` datetime not null,
  primary key (`id`),
  key `idx_ss_matches_user_id` (`user_id`),
  key `idx_ss_matches_resume_id` (`resume_id`),
  key `idx_ss_matches_job_id` (`job_id`),
  constraint `fk_ss_matches_user` foreign key (`user_id`) references `ss_users` (`id`) on delete cascade,
  constraint `fk_ss_matches_resume` foreign key (`resume_id`) references `ss_resumes` (`id`) on delete cascade,
  constraint `fk_ss_matches_job` foreign key (`job_id`) references `ss_jobs` (`id`) on delete cascade
) engine=innodb default charset=utf8mb4 collate=utf8mb4_unicode_ci;

create table if not exists `ss_skills` (
  `id` int not null auto_increment,
  `name` varchar(100) not null,
  `category` varchar(100) not null,
  primary key (`id`),
  unique key `idx_ss_skills_name` (`name`),
  key `idx_ss_skills_category` (`category`)
) engine=innodb default charset=utf8mb4 collate=utf8mb4_unicode_ci;
