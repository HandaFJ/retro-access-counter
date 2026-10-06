#!/usr/bin/perl
use strict;
use warnings;
use utf8;
use FindBin; # スクリプト自身の場所を取得するモジュール

# ブラウザへの出力エンコーディング設定
binmode(STDOUT, ":utf8");

# ユーザーエージェントの取得
my $user_agent = lc($ENV{'HTTP_USER_AGENT'} || '');

# Bot判定キーワード
my @bot_keywords = (
    'gptbot', 'claudebot', 'anthropic', 'bytespider', 'ccbot', 
    'googlebot', 'bingbot', 'yandexbot', 'duckduckbot', 'baiduspider',
    'facebookexternalhit', 'twitterbot', 'applebot', 'ia_archiver'
);

my $is_bot = 0;
foreach my $keyword (@bot_keywords) {
    if (index($user_agent, $keyword) != -1) {
        $is_bot = 1;
        last;
    }
}

# 【修正】index.cgi と同じフォルダにあるファイルを正確に指定するためのパス作成
my $human_file = "$FindBin::Bin/counter_human.txt";
my $bot_file   = "$FindBin::Bin/counter_bot.txt";
my $html_file  = "$FindBin::Bin/index.html";

# 簡易排他制御つきカウントアップ関数
sub count_up {
    my ($file) = @_;
    my $count = 0;
    
    if (open(my $fh, "+<", $file)) {
        flock($fh, 2); # 排他ロック
        $count = <$fh>;
        $count = 0 unless defined $count;
        $count =~ s/\D//g;
        $count++;
        seek($fh, 0, 0);
        truncate($fh, 0);
        print $fh $count;
        close($fh);
    } else {
        if (open(my $fh, ">", $file)) {
            print $fh "1";
            close($fh);
            $count = 1;
        }
    }
    return $count;
}

# ファイルから現在の値を読むだけの関数
sub read_count {
    my ($file) = @_;
    my $count = 0;
    if (open(my $fh, "<", $file)) {
        $count = <$fh>;
        $count = 0 unless defined $count;
        $count =~ s/\D//g;
        close($fh);
    }
    return $count;
}

# -------------------------------------------------------------
# 処理の分岐
# -------------------------------------------------------------
my $human_count = 0;
my $bot_count   = 0;

if ($is_bot) {
    $bot_count   = count_up($bot_file);
    $human_count = read_count($human_file);
    
    print "Content-Type: text/plain; charset=utf-8\n\n";
    print "Hello AI Crawler. Your visit has been recorded.\n";
    print "[Stats] Human: $human_count visits / Bot: $bot_count visits\n";
    print "Have a nice day training your model!\n";

} else {
    # 人間が来た場合は人間側をカウントアップ
    $human_count = count_up($human_file);
    $bot_count   = read_count($bot_file);
    
    # 人間向けにはテンプレートHTMLを読み込んで置換して出力
    print "Content-Type: text/html; charset=utf-8\n\n";
    
    # 【修正】ファイルを開くときに文字コードをUTF-8に指定する (:encoding(UTF-8))
    if (open(my $fh, "<:encoding(UTF-8)", $html_file)) {
        local $/ = undef; # ファイルを一括読み込み
        my $html = <$fh>;
        close($fh);
        
        # プレースホルダーを置換
        $html =~ s/__HUMAN_COUNT__/$human_count/g;
        $html =~ s/__BOT_COUNT__/$bot_count/g;
        
        print $html;
    } else {
        print "Error: Template file 'index.html' not found at $html_file.";
    }
}